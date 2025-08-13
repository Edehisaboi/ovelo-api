import datetime
import json
import asyncio
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from application.core.logging import get_logger
from application.core.dependencies import (
    aws_stt_client,
    mongo_manager,
    ws_connection_manager,
    rekognition_client,
    close_rekognition_client,
)
from application.api.v1.endpoints.ws.helpers.pipeline import IdentificationPipeline, MediaResultPayload
from application.api.v1.ws_manager import ConnectionManager
from external.clients.transcribe import AWSTranscribeRealtimeSTTClient
from external.clients.rekognition import RekognitionClient
from infrastructure.database.mongodb import MongoCollectionsManager

router = APIRouter()
logger = get_logger(__name__)


_IDENTIFICATION_PIPELINES: dict[str, IdentificationPipeline] = {}


def _get_or_create_pipeline(session_id: Optional[str]) -> IdentificationPipeline:
    sid = session_id or "default"
    pipeline = _IDENTIFICATION_PIPELINES.get(sid)
    if not pipeline:
        pipeline = IdentificationPipeline(sid)
        _IDENTIFICATION_PIPELINES[sid] = pipeline
    return pipeline

async def _kickoff_identification_if_needed(
    pipeline: IdentificationPipeline,
    mongodb: MongoCollectionsManager,
    ws_manager: ConnectionManager,
    connection_id: str,
):
    async def on_update(payload: dict):
        #await ws_manager.send_msg(payload, connection_id)
        return

    if not (pipeline._run_task and not pipeline._run_task.done()):
        pipeline.start(run_coro=pipeline.run(mongo_db=mongodb, on_update=on_update))

        async def _forward_final():
            try:
                result: MediaResultPayload = await pipeline.wait_final_result()
                await ws_manager.send_msg(result.model_dump(), connection_id)
                # After delivering the final result, shutdown the pipeline to stop STT and clear state
                try:
                    await pipeline.close()
                except Exception as e:
                    logger.warning(f"Failed to close pipeline after final result: {e}")
            except asyncio.CancelledError:
                # Task cancelled during shutdown; nothing else to do
                return
            except Exception as e:
                logger.error(f"Error sending final identification result: {e}")

        asyncio.create_task(_forward_final())


@router.websocket("/ws/identify")
async def media_identification_websocket(
    websocket: WebSocket,
    mongodb: MongoCollectionsManager = Depends(mongo_manager),
    rekognition: RekognitionClient = Depends(rekognition_client),
    stt: AWSTranscribeRealtimeSTTClient = Depends(aws_stt_client),
):
    """WebSocket endpoint for real-time media identification.
    Receives `frame` and `audio` messages and updates a per-session pipeline."""
    connection_id = None
    ws_manager = ws_connection_manager()

    try:
        connection_id = await ws_manager.connect(websocket)

        # Optional: initial confirmation (kept, not the identification results)
        await ws_manager.send_msg(
            {"type": "connected", "connection_id": connection_id},
            connection_id,
        )

        while True:
            try:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Received non-JSON message on WebSocket; ignoring")
                    continue

                msg_type = msg.get("type")
                if not msg_type:
                    continue

                if msg_type == "ping":
                    await _handle_ping(connection_id, ws_manager)
                    continue

                data = msg.get("data") or {}
                session_id = data.get("sessionId")
                pipeline = _get_or_create_pipeline(session_id or connection_id)

                if msg_type == "frame":
                    frame_obj = data.get("frame") or {}
                    await _handle_frame_data(frame_obj, pipeline, rekognition, mongodb, ws_manager, connection_id)

                elif msg_type == "audio":
                    audio_obj = data.get("audio") or {}
                    await _handle_audio_chunk(audio_obj, pipeline, stt, mongodb, ws_manager, connection_id)

                else:
                    logger.warning(f"Unknown WS message type: {msg_type}")

            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"WS loop error: {e}")
                if not ws_manager.is_connected(connection_id):
                    break
                # Continue processing next messages
                continue

    except WebSocketDisconnect:
        # Client disconnected during handshake or early
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id is not None:
            # Properly close the socket and remove from manager
            try:
                await ws_manager.close_connection(connection_id)
            except Exception as e:
                logger.warning(f"Failed to close WebSocket connection cleanly {connection_id}: {e}")
            # Cleanup: sessionID equals connection_id
            try:
                sid: str = connection_id
                pipeline = _IDENTIFICATION_PIPELINES.pop(sid, None)
                if pipeline:
                    await pipeline.close()
            except Exception as e:
                logger.error(f"Error closing session pipeline {connection_id}: {e}")
        # Ensure Rekognition client is closed to avoid leaks
        try:
            await close_rekognition_client()
        except Exception as e:
            logger.error(f"Error closing Rekognition client: {e}")


async def _handle_frame_data(
    frame_message: Dict[str, Any],
    pipeline: IdentificationPipeline,
    rekognition: RekognitionClient,
    mongodb: MongoCollectionsManager,
    ws_manager: ConnectionManager,
    connection_id: str
):
    """Process a single frame: call Rekognition and update pipeline actors."""
    try:
        frame_b64 = frame_message.get("data")
        if not frame_b64:
            return

        result = await rekognition.recognize_actors(frame_b64)
        actor_names = [c.name.lower() for c in result.celebrities]
        pipeline.update_actors(actor_names)
        await _kickoff_identification_if_needed(pipeline, mongodb, ws_manager, connection_id)
    except Exception as e:
        logger.error(f"Error in processing frame: {e}")


async def _handle_audio_chunk(
    audio_message: Dict[str, Any],
    pipeline: IdentificationPipeline,
    stt: AWSTranscribeRealtimeSTTClient,
    mongodb: MongoCollectionsManager,
    ws_manager: ConnectionManager,
    connection_id: str
):
    """Process a single audio chunk: enqueue and ensure STT stream is running."""
    try:
        audio_b64 = audio_message.get("data")
        if not audio_b64:
            return
        await pipeline.push_audio_chunk(audio_b64)
        pipeline.ensure_stt_stream(stt)
        await _kickoff_identification_if_needed(pipeline, mongodb, ws_manager, connection_id)
    except Exception as e:
        logger.error(f"Error in processing audio: {e}")

async def _handle_ping(connection_id: str, ws_manager):
    try:
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
