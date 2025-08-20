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
    """Compile the graph (if needed) and run it exactly once per connection.
    The run task is tracked by ws_manager so it is cancelled if the client disconnects."""
    lock = _get_lock(connection_id)
    async with lock:
        if transcriber.session_started:
            return

        if transcriber.graph is None:
            builder = create_vrecognition_graph(transcriber, mongo_db)
            graph = builder.compile()  # graph loops internally via Transcriber.run
            transcriber.graph = graph
            transcriber.graph_config = {
                "configurable": {"thread_id": connection_id},
                "callbacks": [OpikTracer(graph=graph.get_graph(xray=True))]
            }

        async def _run_session():
            try:
                if not ws_manager.is_connected(connection_id):
                    return

                output_state = await transcriber.graph.ainvoke(
                    {"start_time": time.monotonic(), "end": False},
                    config=transcriber.graph_config,
                )

                payload = cast(Dict[str, Any], output_state.get("metadata") or {})
                if not payload:
                    payload = {
                        "type": "result",
                        "success": False,
                        "data": {},
                    }

                await ws_manager.send_msg(connection_id, payload)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Graph invoke error for {connection_id}: {e}")
                await ws_manager.send_err_msg(connection_id, "Internal error during recognition.")
            finally:
                # Close transcriber resources and socket
                with suppress(Exception):
                    await transcriber.close()
                await ws_manager.close_connection(connection_id)

        transcriber.session_started = True
        transcriber.invoke_task = asyncio.create_task(_run_session(), name=f"{connection_id}:graph-run")
        # Ensure it gets cancelled if the connection dies
        ws_manager.track_task(connection_id, transcriber.invoke_task)


@router.websocket("/ws/identify")
async def vrecognition_websocket(
    websocket:   WebSocket,
    mongodb:     MongoCollectionsManager = Depends(mongo_manager),
    rekognition: RekognitionClient       = Depends(rekognition_client),
    stt:         AWSTranscribeRealtimeSTTClient = Depends(aws_stt_client),
):
    """WebSocket endpoint for real-time video recognition (VRecognition).
    - Client connects and streams 'frame' and 'audio' messages.
    - We lazily start the graph on first meaningful input.
    - We send exactly one 'result' (or empty) and then close.
    - If the client disconnects early, the graph task is cancelled."""
    ws_manager = ws_connection_manager()
    connection_id: Optional[str] = None

    # Use the manager's session for automatic registration and clean-up
    async with ws_manager.session(websocket) as cid:
        connection_id = cid

        # Initial confirmation handshake
        await ws_manager.send_msg(
            connection_id,
            {"type": "connected", "connection_id": connection_id},
        )

        # Main receive loop: exits when client closes or server closes the socket
        while ws_manager.is_connected(connection_id):
            try:
                raw_json_data = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
            except Exception as e:
                if not ws_manager.is_connected(connection_id):
                    logger.info(f"Client not connected; stopping loop for {connection_id}: {e}")
                    break
                logger.error(f"WebSocket receive error for {connection_id}: {e}")
                continue

            try:
                msg = json.loads(raw_json_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON on WebSocket {connection_id}: {e}")
                continue

            msg_type = msg.get("type")
            if not msg_type:
                continue

            if msg_type == "ping":
                await _handle_ping(connection_id, ws_manager)
                continue

            data = msg.get("data") or {}
            transcriber = _get_or_create_session(connection_id)

            if msg_type == "frame":
                await _handle_frame_data(data.get("frame") or {}, transcriber, rekognition, mongodb, ws_manager, connection_id)

            elif msg_type == "audio":
                await _handle_audio_chunk(data.get("audio") or {}, transcriber, stt, mongodb, ws_manager, connection_id)

            else:
                logger.warning(f"Unknown WS message type: {msg_type}")

    try:
        if connection_id:
            transcriber = _SESSIONS.pop(connection_id, None)
            if transcriber:
                task = transcriber.invoke_task
                if task and not task.done():
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
                with suppress(Exception):
                    await transcriber.close()
            # Remove the start lock for this connection
            _RUN_LOCKS.pop(connection_id, None)
    finally:
        # Ensure external clients are closed
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

        # Start graph on first meaningful input
        if not transcriber.session_started:
            await _ensure_started_once(transcriber, mongodb, ws_manager, connection_id)

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error processing frame for {connection_id}: {e}")


async def _handle_audio_chunk(
    audio_data:     Dict[str, Any],
    transcriber:    Transcriber,
    stt:            AWSTranscribeRealtimeSTTClient,
    mongodb:        MongoCollectionsManager,
    ws_manager:     ConnectionManager,
    connection_id:  str
):
    try:
        audio_b64 = audio_data.get("data")
        if not audio_b64:
            return

        await transcriber.push_audio_chunk(audio_b64)
        transcriber.ensure_stt_stream(stt)

        # Start graph on first meaningful input
        if not transcriber.session_started:
            await _ensure_started_once(transcriber, mongodb, ws_manager, connection_id)

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error processing audio for {connection_id}: {e}")


async def _handle_ping(connection_id: str, ws_manager: ConnectionManager):
    try:
        if not ws_manager.is_connected(connection_id):
            return
        await ws_manager.send_msg(
            connection_id,
            {
                "status": "pong",
                "message": "Connection_alive",
                "timestamp": datetime.datetime.now().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"Error handling ping for {connection_id}: {e}")
        await ws_manager.send_err_msg(connection_id, f"Ping failed: {str(e)}")
