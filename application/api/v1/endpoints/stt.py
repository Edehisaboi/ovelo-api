from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
import json

from application.services.transcription.stt import stt_service
from application.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription."""
    await websocket.accept()
    logger.info("WebSocket connection established for transcription")
    
    try:
        async def audio_generator():
            """Generate audio chunks from WebSocket messages."""
            while True:
                try:
                    # Receive audio data from client
                    data = await websocket.receive_bytes()
                    yield data
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error receiving audio data: {e}")
                    break
        
        # Start transcription
        async for result in stt_service.transcribe_external_stream(
            audio_generator(),
            on_partial=lambda text: websocket.send_text(json.dumps({
                "type": "partial",
                "text": text
            })),
            on_final=lambda text: websocket.send_text(json.dumps({
                "type": "final", 
                "text": text
            })),
            on_error=lambda error: websocket.send_text(json.dumps({
                "type": "error",
                "error": error
            }))
        ):
            # Send result to client
            await websocket.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket transcription error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e)
            }))
        except:
            pass


@router.post("/transcribe/microphone")
async def transcribe_microphone():
    """Start microphone transcription (streaming response)."""
    try:
        async def generate_transcription():
            """Generate transcription results."""
            async for result in stt_service.transcribe_microphone():
                yield f"data: {json.dumps(result)}\n\n"
        
        return StreamingResponse(
            generate_transcription(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        logger.error(f"Microphone transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe/stream")
async def transcribe_stream():
    """Transcribe from external audio stream (streaming response)."""
    try:
        # This would typically receive audio data from the request body
        # For now, we'll return an error indicating this needs implementation
        raise HTTPException(
            status_code=501, 
            detail="Stream transcription endpoint not yet implemented"
        )
    except Exception as e:
        logger.error(f"Stream transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 