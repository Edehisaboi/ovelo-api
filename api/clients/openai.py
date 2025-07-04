import json
import asyncio
from typing import AsyncGenerator, Optional, Callable

import websockets
from langchain_openai import OpenAIEmbeddings

from config import settings
from config.logging import get_logger

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
    def embeddings(self) -> OpenAIEmbeddings:
        """Get the underlying OpenAI embeddings instance."""
        return self._embeddings

    async def create_embedding(self, text: str) -> list[float]:
        """Create embedding for a single text."""
        return await self._embeddings.aembed_query(text)

    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts."""
        return await self._embeddings.aembed_documents(texts)


class OpenAISTT:
    """OpenAI realtime speech-to-text client using WebSocket API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with an API key and base URL."""
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_STT_BASE_URL

    async def transcribe_stream(
            self,
            audio_stream:   AsyncGenerator[bytes, None],
            model:          str = settings.OPENAI_STT_MODEL,
            language:       Optional[str] = None,
            prompt:         Optional[str] = None,
            response_format: str = "verbose_json",
            temperature:    float = 0.0,
            on_partial:     Optional[Callable[[str], None]] = None,
            on_final:       Optional[Callable[[str], None]] = None,
            on_error:       Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Stream audio to OpenAI's realtime transcription API and yield results.

        Args:
            audio_stream: Async generator yielding audio chunks as bytes.
            model: Whisper model to use (e.g., "whisper-1").
            language: Language code (e.g., "en-US"); if None, auto-detection may occur.
            prompt: Optional context prompt for transcription.
            response_format: Format of the API response (e.g., "verbose_json").
            temperature: Sampling temperature for transcription decoding.
            on_partial: Callback for partial transcription results.
            on_final: Callback for final transcription results.
            on_error: Callback for error messages.

        Yields:
            dict: Transcription results or error messages with keys like "type", "text", "error".
        """
        # Build WebSocket URL with query parameters
        params = {
            #"type": "start",
            "model":            model,
            "sampling_rate":    16000,  # Common sampling rate for audio
            "temperature":      temperature,
            "response_format":  response_format,
        }
        # Only include optional parameters if provided
        if language:
            params["language"] = language
        if prompt:
            params["prompt"] = prompt

        url = f"{self.base_url}?{self._build_query_string(params)}"

        try:
            async with websockets.connect(
                    url,
                    extra_headers={"Authorization": f"Bearer {self.api_key}"}
            ) as websocket:
                logger.info("Connected to OpenAI realtime transcription API")

                # Start streaming audio in a separate task
                audio_task = asyncio.create_task(self._stream_audio(websocket, audio_stream))

                try:
                    # Process incoming WebSocket messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            result = self._process_response(data)

                            if result:
                                yield result
                                # Trigger callbacks based on result type
                                if result.get("type") == "partial" and on_partial:
                                    on_partial(result.get("text", ""))
                                elif result.get("type") == "final" and on_final:
                                    on_final(result.get("text", ""))

                        except json.JSONDecodeError as e:
                            error_msg = f"Failed to parse response: {e}"
                            logger.error(error_msg)
                            if on_error:
                                on_error(error_msg)
                            yield {"type": "error", "error": error_msg}

                except websockets.exceptions.ConnectionClosed as e:
                    logger.info(f"WebSocket connection closed: {e}")

                except Exception as e:
                    error_msg = f"Error processing transcription: {e}"
                    logger.error(error_msg)
                    if on_error:
                        on_error(error_msg)
                    yield {"type": "error", "error": error_msg}

                finally:
                    # Ensure audio task is cleaned up
                    audio_task.cancel()
                    try:
                        await audio_task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            error_msg = f"Failed to connect to OpenAI API: {e}"
            logger.error(error_msg)
            if on_error:
                on_error(error_msg)
            yield {"type": "error", "error": error_msg}

    @staticmethod
    async def _stream_audio(websocket, audio_stream: AsyncGenerator[bytes, None]):
        """Stream audio chunks to the WebSocket."""
        try:
            async for audio_chunk in audio_stream:
                await websocket.send(audio_chunk)  # Send raw bytes as binary message
        except Exception as e:
            logger.error(f"Error streaming audio: {e}")
            raise

    @staticmethod
    def _process_response(data: dict) -> Optional[dict]:
        """Process and format transcription response from the API."""
        try:
            if "error" in data:
                return {
                    "type": "error",
                    "error": data["error"].get("message", "Unknown error")
                }

            text = data.get("text", "")
            if not text:
                return None

            is_final = data.get("final", False)

            return {
                "type": "final" if is_final else "partial",
                "text": text,
                "timestamp": data.get("timestamp", 0),
                "confidence": data.get("confidence", 0.0),
                "language": data.get("language"),
                "language_probability": data.get("language_probability")
            }

        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {"type": "error", "error": str(e)}

    @staticmethod
    def _build_query_string(params: dict) -> str:
        """Build URL-encoded query string from parameters."""
        import urllib.parse
        return urllib.parse.urlencode(params)