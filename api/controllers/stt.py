import json
from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse

from api.services.stt.service import STTService
from config.dependencies import get_stt_service
from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])


@router.websocket("/microphone")
async def microphone_transcription(
    websocket: WebSocket,
    stt_service: STTService = Depends(get_stt_service)
):
    """
    WebSocket endpoint for real-time microphone transcription.
    
    Connects to client's microphone and streams transcription results.
    """
    await websocket.accept()
    logger.info("WebSocket connection established for microphone transcription")
    
    try:
        # Callbacks for WebSocket communication
        async def on_partial(text: str):
            await websocket.send_text(json.dumps({
                "type": "partial",
                "text": text
            }))
        
        async def on_final(text: str):
            await websocket.send_text(json.dumps({
                "type": "final", 
                "text": text
            }))
        
        async def on_error(error: str):
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": error
            }))
        
        # Start transcription
        async for result in stt_service.transcribe_microphone(
            on_partial=on_partial,
            on_final=on_final,
            on_error=on_error
        ):
            # Send result to client
            await websocket.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in microphone transcription: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e)
            }))
        except:
            pass


@router.websocket("/stream")
async def external_stream_transcription(
    websocket: WebSocket,
    stt_service: STTService = Depends(get_stt_service)
):
    """
    WebSocket endpoint for external audio stream transcription.
    
    Receives audio chunks from client and returns transcription results.
    """
    await websocket.accept()
    logger.info("WebSocket connection established for external stream transcription")
    
    try:
        # Callbacks for WebSocket communication
        async def on_partial(text: str):
            await websocket.send_text(json.dumps({
                "type": "partial",
                "text": text
            }))
        
        async def on_final(text: str):
            await websocket.send_text(json.dumps({
                "type": "final",
                "text": text
            }))
        
        async def on_error(error: str):
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": error
            }))
        
        async def audio_stream() -> AsyncGenerator[bytes, None]:
            """Receive audio chunks from WebSocket."""
            try:
                while True:
                    # Receive audio chunk from client
                    audio_chunk = await websocket.receive_bytes()
                    yield audio_chunk
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during audio streaming")
                raise
        
        # Start transcription
        async for result in stt_service.transcribe_external_stream(
            audio_stream(),
            on_partial=on_partial,
            on_final=on_final,
            on_error=on_error
        ):
            # Send result to client
            await websocket.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in external stream transcription: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e)
            }))
        except:
            pass


@router.get("/health")
async def health_check():
    """Health check endpoint for STT service."""
    return {"status": "healthy", "service": "stt"} 