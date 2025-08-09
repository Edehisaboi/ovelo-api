import asyncio
import base64
from pprint import pprint
from typing import Optional, Callable, Awaitable

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.auth import StaticCredentialResolver
from amazon_transcribe.model import TranscriptEvent

from application.core.logging import get_logger
from application.core.config import settings


logger = get_logger(__name__)


def _map_language_to_aws(language: str) -> str:
    """Map generic or lowercase language code to AWS Transcribe enum format."""
    if not language:
        return "en-US"

    lang = language.strip()
    # If already matches AWS enum (case-sensitive), just return
    aws_codes = {
        "en-IE", "ar-AE", "zh-TW", "zh-HK", "en-US", "uk-UA", "en-AB", "en-IN", "ar-SA", "zh-CN", "eu-ES",
        "en-ZA", "tl-PH", "so-SO", "sk-SK", "ru-RU", "ro-RO", "lv-LV", "id-ID", "hr-HR", "fi-FI", "pl-PL",
        "no-NO", "nl-NL", "pt-PT", "es-ES", "th-TH", "de-DE", "it-IT", "fr-FR", "sr-RS", "af-ZA", "en-NZ",
        "ko-KR", "el-GR", "de-CH", "hi-IN", "vi-VN", "ms-MY", "he-IL", "cs-CZ", "gl-ES", "da-DK", "en-AU",
        "zu-ZA", "en-WL", "pt-BR", "fa-IR", "sv-SE", "ja-JP", "ca-ES", "es-US", "fr-CA", "en-GB"
    }
    if lang in aws_codes:
        return lang

    # Normalise lowercase or missing region to AWS standard
    lang = lang.lower()
    mapping = {
        "en": "en-US",
        "es": "es-US",
        "fr": "fr-CA",
        "de": "de-DE",
        "it": "it-IT",
        "pt": "pt-PT",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "zh": "zh-CN",
    }
    return mapping.get(lang, "en-US")


class _AWSResultHandler(TranscriptResultStreamHandler):
    """Internal handler that forwards partial/final transcripts via callback."""

    def __init__(self, output_stream, on_transcript: Optional[Callable[[dict], Awaitable[None]]]):
        super().__init__(output_stream)
        self._on_transcript = on_transcript

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        if not self._on_transcript:
            return

        results = transcript_event.transcript.results
        for result in results:
            # Choose first alternative if present
            text = ""
            if result.alternatives:
                text = result.alternatives[0].transcript or ""

            payload = {
                "is_partial": result.is_partial,
                "text": text
            }

            try:
                await self._on_transcript(payload)
            except Exception as e:
                logger.error(f"on_transcript callback failed: {e}")


class AWSTranscribeRealtimeSTTClient:
    """AWS Transcribe streaming client for real-time speech-to-text transcription.
    The audio_chunk_generator must yield base64-encoded PCM16 audio chunks."""

    def __init__(self) -> None:
        self._client = TranscribeStreamingClient(
            region=settings.AWS_REGION,
            credential_resolver=StaticCredentialResolver(
                access_key_id=settings.AWS_ACCESS_KEY_ID,
                secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        )

    @staticmethod
    def _infer_sample_rate(input_audio_format: str) -> int:
        fmt = (input_audio_format or "").lower()
        # Default to 16,000 for PCM16
        if "pcm16" in fmt or "pcm" in fmt:
            return 16000
        return 16000

    async def transcribe(
        self,
        audio_chunk_generator,
        on_transcript: Optional[Callable[[dict], Awaitable[None]]] = None,
        language: str = settings.AWS_STT_LANGUAGE,
        input_audio_format: str = settings.AWS_STT_INPUT_AUDIO_FORMAT
    ) -> None:
        language_code = _map_language_to_aws(language)
        sample_rate = self._infer_sample_rate(input_audio_format)

        stream = await self._client.start_stream_transcription(
            language_code=language_code,
            media_sample_rate_hz=sample_rate,
            media_encoding="pcm",
        )

        handler = _AWSResultHandler(stream.output_stream, on_transcript)

        async def _send_audio():
            async for chunk in audio_chunk_generator:
                if chunk is None:
                    break
                try:
                    # Expect base64-encoded audio
                    if isinstance(chunk, str):
                        audio_bytes = base64.b64decode(chunk)
                    else:
                        audio_bytes = chunk  # bytes-like
                    await stream.input_stream.send_audio_event(audio_chunk=audio_bytes)
                except Exception as e:
                    logger.error(f"Failed sending audio chunk: {e}")
                    break
            try:
                await stream.input_stream.end_stream()
            except Exception as e:
                logger.warning(f"Failed to close audio input stream: {e}")

        await asyncio.gather(_send_audio(), handler.handle_events())


