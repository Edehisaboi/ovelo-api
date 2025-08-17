import json
import time
import asyncio
import datetime
from typing import Any, Dict, Optional, cast

from contextlib import suppress
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from opik.integrations.langchain import OpikTracer

from application.api.v1.ws_manager import ConnectionManager
from application.core.dependencies import (
    aws_stt_client,
    rekognition_client,
    close_rekognition_client,
    mongo_manager,
    ws_connection_manager,
)
from application.core.logging import get_logger
from application.services.vRecognition.agents.Transcriber import Transcriber
from application.services.vRecognition.graph import create_vrecognition_graph
from external.clients.rekognition import RekognitionClient
from external.clients.transcribe import AWSTranscribeRealtimeSTTClient
from infrastructure.database.mongodb import MongoCollectionsManager

router = APIRouter()
logger = get_logger(__name__)


# Active session processors keyed by connection ID
_SESSIONS:  dict[str, Transcriber]  = {}
_RUN_LOCKS: dict[str, asyncio.Lock] = {}


def _get_or_create_session(connection_id: Optional[str]) -> Transcriber:
    if not connection_id:
        raise ValueError("Connection ID must be provided to get or create a session.")
    transcriber = _SESSIONS.get(connection_id)
    if transcriber is None:
        transcriber = Transcriber(connection_id, 60)
        _SESSIONS[connection_id] = transcriber
    return transcriber

def _get_lock(connection_id: str) -> asyncio.Lock:
    lock = _RUN_LOCKS.get(connection_id)
    if lock is None:
        lock = asyncio.Lock()
        _RUN_LOCKS[connection_id] = lock
    return lock

async def _ensure_started_once(
    transcriber:    Transcriber,
    mongo_db:       MongoCollectionsManager,
    ws_manager:     ConnectionManager,
    connection_id:  str,
) -> None:
    lock = _get_lock(connection_id)
    async with lock:
        # If we've ever started this session, never start again.
        if transcriber.session_started:
            return

        # First (and only) start: compile and run
        if not transcriber.session_started:
            if transcriber.graph is None:
                builder = create_vrecognition_graph(transcriber, mongo_db)
                graph = builder.compile()  # this graph should loop back to Transcriber.run
                transcriber.graph = graph
                transcriber.graph_config = {
                    "configurable": {"thread_id": connection_id},
                    "callbacks": [OpikTracer(graph=graph.get_graph(xray=True))],
                    "recursion_limit": 50,
                }

        async def _run_session():
            try:
                if not ws_manager.is_connected(connection_id):
                    return

                output_state = await transcriber.graph.ainvoke(
                    {"start_time": time.monotonic(), "end": False},
                    config=transcriber.graph_config,
                )
                payload = output_state.get("metadata")
                if payload and ws_manager.is_connected(connection_id):
                    await ws_manager.send_msg(cast(Dict[str, Any], payload), connection_id)

                if output_state.get("end") and ws_manager.is_connected(connection_id):
                    # TODO: send empty payload to indicate end of session
                    # No match found, send empty result
                    pass
                await transcriber.close()
                await ws_manager.close_connection(connection_id)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Graph invoke error: {e}")

        transcriber.session_started = True
        transcriber.invoke_task = asyncio.create_task(_run_session())



@router.websocket("/ws/identify")
async def vrecognition_websocket(
    websocket:   WebSocket,
    mongodb:     MongoCollectionsManager = Depends(mongo_manager),
    rekognition: RekognitionClient = Depends(rekognition_client),
    stt:         AWSTranscribeRealtimeSTTClient = Depends(aws_stt_client),
):
    """WebSocket endpoint for real-time video recognition (VRecognition).
    Receives `frame` and `audio` messages and runs a per-session graph."""
    connection_id: Optional[str] = None
    ws_manager = ws_connection_manager()

    try:
        connection_id = await ws_manager.connect(websocket)

        # initial confirmation handshake
        await ws_manager.send_msg(
            {"type": "connected", "connection_id": connection_id},
            connection_id,
        )

        while True:
            try:
                raw_json_data = await websocket.receive_text()
                msg = json.loads(raw_json_data)

                msg_type = msg.get("type")
                if not msg_type:
                    continue

                if msg_type == "ping":
                    await _handle_ping(connection_id, ws_manager)
                    continue

                data = msg.get("data") or {}
                transcriber = _get_or_create_session(connection_id)

                if msg_type == "frame":
                    frame_obj = data.get("frame") or {}
                    await _handle_frame_data(frame_obj, transcriber, rekognition, mongodb, ws_manager, connection_id)

                elif msg_type == "audio":
                    audio_obj = data.get("audio") or {}
                    await _handle_audio_chunk(audio_obj, transcriber, stt, mongodb, ws_manager, connection_id)

                else:
                    logger.warning(f"Unknown WS message type: {msg_type}")

            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Received invalid JSON data on WebSocket: {e}")
                continue
            except Exception as e:
                if not ws_manager.is_connected(connection_id):
                    logger.info(f"Client not connected; stopping loop for {connection_id}: {e}")
                    break
                logger.error(f"Websocket error: {e}")
                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id and ws_manager.is_connected(connection_id):
            with suppress(Exception):
                await ws_manager.close_connection(connection_id)

        transcriber = _SESSIONS.pop(connection_id, None)
        if transcriber:
            task = getattr(transcriber, "invoke_task", None)
            if task and not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            await transcriber.close()

        _RUN_LOCKS.pop(connection_id, None)
        with suppress(Exception):
            await close_rekognition_client()


async def _handle_frame_data(
    frame_data:     Dict[str, Any],
    transcriber:    Transcriber,
    rekognition:    RekognitionClient,
    mongodb:        MongoCollectionsManager,
    ws_manager:     ConnectionManager,
    connection_id:  str
):
    try:
        frame_b64 = frame_data.get("data")
        if not frame_b64:
            return
        result = await rekognition.recognize_actors(frame_b64)
        actor_names = [c.name.lower() for c in result.celebrities if c.name]
        if actor_names:
            transcriber.update_actors(actor_names)
            if not transcriber.session_started:
                await _ensure_started_once(transcriber, mongodb, ws_manager, connection_id)
    except Exception as e:
        logger.error(f"Error in processing frame: {e}")


async def _handle_audio_chunk(
    audio_data:     Dict[str, Any],
    transcriber:    Transcriber,
    stt:            AWSTranscribeRealtimeSTTClient,
    mongodb:        MongoCollectionsManager,
    ws_manager:     ConnectionManager,
    connection_id:  str
):
    """Process a single audio chunk: enqueue and ensure STT stream is running."""
    try:
        audio_b64 = audio_data.get("data")
        if not audio_b64:
            return
        await transcriber.push_audio_chunk(audio_b64)
        transcriber.ensure_stt_stream(stt)
        if not transcriber.session_started:
            await _ensure_started_once(transcriber, mongodb, ws_manager, connection_id)
    except Exception as e:
        logger.error(f"Error in processing audio: {e}")


async def _handle_ping(connection_id: str, ws_manager):
    try:
        if not ws_manager.is_connected(connection_id):
            return
        await ws_manager.send_msg(
            {
                "status": "pong",
                "message": "Connection_alive",
                "timestamp": datetime.datetime.now().isoformat(),
            },
            connection_id,
        )
    except Exception as e:
        logger.error(f"Error handling ping: {e}")
        await ws_manager.send_err_msg(connection_id, f"Ping failed: {str(e)}")
