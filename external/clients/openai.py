from typing import Optional, Dict, Any, List

import httpx
from langchain_openai import OpenAIEmbeddings

from .base import AbstractAPIClient
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


class OpenAIRealtimeSTTClient(AbstractAPIClient):
    """API client for creating OpenAI Realtime Transcription sessions."""

    MODEL = settings.OPENAI_STT_MODEL
    LANGUAGE = settings.OPENAI_STT_LANGUAGE
    PROMPT = settings.OPENAI_STT_PROMPT
    EXPIRE_SECONDS = settings.OPENAI_STT_TOKEN_EXPIRY
    AUDIO_FORMAT = settings.OPENAI_STT_INPUT_AUDIO_FORMAT
    NOISE_REDUCTION_TYPE = settings.OPENAI_STT_NOISE_REDUCTION_TYPE
    TURN_DETECTION_TYPE = settings.OPENAI_STT_TURN_DETECTION_TYPE
    TURN_DETECTION_THRESHOLD = settings.OPENAI_STT_TURN_DETECTION_THRESHOLD
    TURN_DETECTION_PREFIX_PADDING_MS = settings.OPENAI_STT_TURN_DETECTION_PREFIX_PADDING_MS
    TURN_DETECTION_SILENCE_DURATION_MS = settings.OPENAI_STT_TURN_DETECTION_SILENCE_DURATION_MS
    MODALITIES = settings.OPENAI_STT_MODALITIES

    def __init__(
        self,
        api_key:        str,
        http_client:    httpx.AsyncClient,
        base_url:       str,
    ) -> None:
        super().__init__(api_key, http_client, base_url, None)

    def _get_headers(self) -> Dict[str, str]:
        """Return headers for OpenAI Realtime API requests."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

    async def create_stt_session(
            self,
            *,
            model: str = MODEL,
            language: str = LANGUAGE,
            prompt: str = PROMPT,
            expire_seconds: int = EXPIRE_SECONDS,
            audio_format: str = AUDIO_FORMAT,
            noise_reduction_type: Optional[str] = NOISE_REDUCTION_TYPE,
            turn_detection_type: Optional[str] = TURN_DETECTION_TYPE,
            turn_detection_threshold: float = TURN_DETECTION_THRESHOLD,
            turn_detection_prefix_padding_ms: int = TURN_DETECTION_PREFIX_PADDING_MS,
            turn_detection_silence_duration_ms: int = TURN_DETECTION_SILENCE_DURATION_MS,
            modalities: Optional[List[str]] = None,
            include: Optional[List[str]] = None,
            extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new OpenAI realtime transcription session."""
        payload: Dict[str, Any] = {
            "client_secret": {
                "expires_at": {
                    "anchor": "created_at",
                    "seconds": expire_seconds
                }
            },
            "input_audio_format": audio_format,
            "input_audio_transcription": {
                "model": model,
                "language": language,
                "prompt": prompt
            },
            "modalities": modalities or self.MODALITIES,
        }

        # Optional: turn_detection (None disables VAD)
        if turn_detection_type:
            payload["turn_detection"] = {
                "type": turn_detection_type,
                "threshold": turn_detection_threshold,
                "prefix_padding_ms": turn_detection_prefix_padding_ms,
                "silence_duration_ms": turn_detection_silence_duration_ms
            }
        else:
            payload["turn_detection"] = None

        # Optional: noise reduction
        if noise_reduction_type:
            payload["input_audio_noise_reduction"] = {"type": noise_reduction_type}
        else:
            payload["input_audio_noise_reduction"] = None

        # Optional: include extra event fields
        if include:
            payload["include"] = include

        # Merge any extra custom fields
        if extra_payload:
            payload.update(extra_payload)

        # POST to /transcription_sessions
        return await self.post("transcription_sessions", json_body=payload)