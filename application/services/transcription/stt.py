import asyncio

from typing import AsyncGenerator, Optional, Callable

from application.core.logging import get_logger
from application.core.dependencies import stt_client
from external.clients.openai import OpenAISTT

logger = get_logger(__name__)


class STTService:
    """Speech-to-Text service using OpenAI's realtime API."""
    
    def __init__(self, client: Optional[OpenAISTT] = None):
        if client is None:
            client = stt_client()
        self.stt_client = client
        
    async def transcribe_microphone(
        self,
        on_partial: Optional[Callable[[str], None]] = None,
        on_final:   Optional[Callable[[str], None]] = None,
        on_error:   Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> AsyncGenerator[dict, None]:
        """
        Transcribe audio from microphone in real-time.
        
        Args:
            on_partial: Callback for partial transcriptions
            on_final: Callback for final transcriptions  
            on_error: Callback for errors
            **kwargs: Additional parameters for transcription
            
        Yields:
            Transcription results
        """
        try:
            # Import here to avoid dependency issues
            import sounddevice as sd
            import numpy as np
            
            # Audio settings
            sample_rate = 16000
            channels = 1
            dtype = np.int16
            chunk_duration = 0.1  # 100ms chunks
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                # Convert to bytes and put in queue
                audio_data = indata.tobytes()
                audio_queue.put_nowait(audio_data)
            
            # Create audio queue
            audio_queue = asyncio.Queue()
            
            async def audio_generator():
                """Generate audio chunks from the queue."""
                try:
                    while True:
                        try:
                            # Get audio chunk with timeout
                            chunk = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
                            yield chunk
                        except asyncio.TimeoutError:
                            # Send silence to keep connection alive
                            silence = np.zeros(int(sample_rate * chunk_duration), dtype=dtype).tobytes()
                            yield silence
                except asyncio.CancelledError:
                    logger.info("Audio generator cancelled")
                    raise
            
            # Start audio stream
            with sd.InputStream(
                callback=audio_callback,
                channels=channels,
                samplerate=sample_rate,
                dtype=dtype,
                blocksize=int(sample_rate * chunk_duration)
            ):
                logger.info("Started microphone transcription")
                
                async for result in self.stt_client.transcribe_stream(
                    audio_generator(),
                    on_partial=on_partial,
                    on_final=on_final,
                    on_error=on_error,
                    **kwargs
                ):
                    yield result
                    
        except ImportError:
            error_msg = "sounddevice not installed. Install with: pip install sounddevice"
            logger.error(error_msg)
            if on_error:
                on_error(error_msg)
            yield {"type": "error", "error": error_msg}
        except Exception as e:
            error_msg = f"Microphone transcription error: {e}"
            logger.error(error_msg)
            if on_error:
                on_error(error_msg)
            yield {"type": "error", "error": error_msg}
    
    async def transcribe_external_stream(
        self,
        audio_stream:   AsyncGenerator[bytes, None],
        on_partial:     Optional[Callable[[str], None]] = None,
        on_final:       Optional[Callable[[str], None]] = None,
        on_error:       Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> AsyncGenerator[dict, None]:
        """
        Transcribe audio from an external stream.
        
        Args:
            audio_stream: Async generator yielding audio chunks
            on_partial: Callback for partial transcriptions
            on_final: Callback for final transcriptions
            on_error: Callback for errors
            **kwargs: Additional parameters for transcription
            
        Yields:
            Transcription results
        """
        try:
            logger.info("Started external stream transcription")
            
            async for result in self.stt_client.transcribe_stream(
                audio_stream,
                on_partial=on_partial,
                on_final=on_final,
                on_error=on_error,
                **kwargs
            ):
                yield result
                
        except Exception as e:
            error_msg = f"External stream transcription error: {e}"
            logger.error(error_msg)
            if on_error:
                on_error(error_msg)
            yield {"type": "error", "error": error_msg}


# Create singleton instance
stt_service = STTService()