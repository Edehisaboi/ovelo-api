import json
import asyncio
import websockets

from langchain_openai import OpenAIEmbeddings
from typing import Optional, Callable, Awaitable
from pydantic import SecretStr

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
            api_key=SecretStr(settings.OPENAI_API_KEY),
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
