import json
import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from application.core.logging import get_logger
from application.core.dependencies import (
    stt_client,
    mongo_manager,
    ws_connection_manager,
    rekognition_client,
    close_rekognition_client,
)
from infrastructure.database.mongodb import MongoCollectionsManager
from external.clients.rekognition import RekognitionClient
from external.clients.openai import OpenAIRealtimeSTTClient
from .pipeline import IdentificationPipeline

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


@router.websocket("/ws/identify")
async def media_identification_websocket(
    websocket: WebSocket,
    mongodb: MongoCollectionsManager = Depends(mongo_manager),
    rekognition: RekognitionClient = Depends(rekognition_client),
    stt: OpenAIRealtimeSTTClient = Depends(stt_client),
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
                msg = json.loads(raw)

                msg_type = msg.get("type")
                if not msg_type:
                    # Keep silent
                    continue

                if msg_type == "ping":
                    await _handle_ping(connection_id, ws_manager)
                    continue

                data = msg.get("data") or {}
                session_id = data.get("sessionId")
                pipeline = _get_or_create_pipeline(session_id)

                if msg_type == "frame":
                    frame_obj = data.get("frame") or {}
                    await _handle_frame_data(frame_obj, pipeline, rekognition)

                elif msg_type == "audio":
                    audio_obj = data.get("audio") or {}
                    await _handle_audio_chunk(audio_obj, pipeline, stt)

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
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id is not None:
            ws_manager.disconnect(connection_id)
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
):
    """Process a single frame: call Rekognition and update pipeline actors."""
    try:
        frame_b64 = frame_message.get("data")
        if not frame_b64:
            return
        result = await rekognition.recognize_actors(frame_b64)
        actor_names = [c.name for c in result.celebrities]
        pipeline.update_actors(actor_names)
        # TODO: trigger identification refinement using pipeline state
    except Exception as e:
        logger.error(f"Error in processing frame: {e}")


async def _handle_audio_chunk(
    audio_message: Dict[str, Any],
    pipeline: IdentificationPipeline,
    stt: OpenAIRealtimeSTTClient,
):
    """Process a single audio chunk: enqueue and ensure STT stream is running."""
    try:
        audio_b64 = audio_message.get("data")
        if not audio_b64:
            return
        await pipeline.push_audio_chunk(audio_b64)
        pipeline.ensure_stt_stream(stt)
        # TODO: trigger identification refinement using pipeline state
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