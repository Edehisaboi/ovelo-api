import json
import asyncio
import websockets

from langchain_openai import OpenAIEmbeddings

from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingClient:
    """OpenAI embedding client implementation with retries and error handling."""
    def __init__(
        self,
        model_name: str = settings.OPENAI_EMBEDDING_MODEL
    ):
        self.model_name = model_name
        self._embeddings = OpenAIEmbeddings(
            model=self.model_name,
            api_key=settings.OPENAI_API_KEY,
            chunk_size=settings.CHUNK_SIZE,
            max_retries=settings.OPENAI_EMBEDDING_MAX_RETRIES,
            retry_min_seconds=settings.OPENAI_EMBEDDING_WAIT_MIN,
            retry_max_seconds=settings.OPENAI_EMBEDDING_WAIT_MAX,
            timeout=settings.OPENAI_EMBEDDING_TIMEOUT
        )

    @property
    def embedding(self) -> OpenAIEmbeddings:
        """Get the underlying OpenAI embeddings instance."""
        return self._embeddings


class OpenAIRealtimeSTTClient:
    def __init__(
        self,
        api_key:        str,
        base_url:       str,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url

        self._header = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }

    @staticmethod
    def session_config(
        model: str = settings.OPENAI_STT_MODEL,
        language: str = settings.OPENAI_STT_LANGUAGE,
        prompt: str = settings.OPENAI_STT_PROMPT,
        input_audio_format: str = settings.OPENAI_STT_INPUT_AUDIO_FORMAT,
        turn_detection: str = settings.OPENAI_STT_TURN_DETECTION_TYPE,
        vad: float = settings.OPENAI_STT_TURN_DETECTION_THRESHOLD,
        noise_reduction: str = settings.OPENAI_STT_NOISE_REDUCTION_TYPE,
    ) -> dict:
        return {
            "type": "transcription_session.update",
            "session": {
                "input_audio_format": input_audio_format,
                "input_audio_transcription": {
                    "model": model,
                    "language": language,
                    "prompt": prompt,
                },
                "turn_detection": {
                    "type": turn_detection,
                    "threshold": vad
                },
                "input_audio_noise_reduction": {
                    "type": noise_reduction,
                }
            },
        }

    async def transcribe(
        self,
        audio_chunk_generator,
        model: str = settings.OPENAI_STT_MODEL,
        **kwargs: dict
    ) -> None:
        async with websockets.connect(self.base_url, additional_headers=self._header, max_size=None) as ws:
            # send session config
            config = self.session_config(model=model, **kwargs)
            await ws.send(json.dumps(config))
            logger.info("Transcription session config sent.")

            # Run sending audio and receiving transcript concurrently
            await asyncio.gather(
                self._send_audio(ws, audio_chunk_generator),
                self._recv_transcripts(ws)
            )

    async def _send_audio(self, ws, audio_chunk_generator):
        logger.info("Starting audio streaming loop...")
        async for chunk in audio_chunk_generator:
            await ws.send({
                "type": "input_audio_buffer.append",
                "audio": chunk
            })
        # End of stream
        await ws.send(json.dumps({"type": "input_audio_buffer.end"}))
        logger.info("Audio streaming loop ended.")

    async def _recv_transcripts(self, ws):
        async for msg in ws:
            data = json.loads(msg)
            if data.get("type") == settings.OPENAI_STT_COMPLETED:
                transcript = data.get("transcript")
                logger.info(f"Transcript: {transcript}")
