import logging
from typing import List

import tiktoken
from openai import OpenAI
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """OpenAI embedding client implementation with retries and error handling."""

    def __init__(
        self,
        client:         OpenAI,
        model_name:     str = settings.OPENAI_EMBEDDING_MODEL,
        max_retries:    int = settings.OPENAI_EMBEDDING_MAX_RETRIES,
        batch_size:     int = settings.OPENAI_EMBEDDING_BATCH_SIZE,
        wait_min:       int = settings.OPENAI_EMBEDDING_WAIT_MIN,
        wait_max:       int = settings.OPENAI_EMBEDDING_WAIT_MAX,
        wait_multiplier: int = settings.OPENAI_EMBEDDING_WAIT_MULTIPLIER
    ):
        self.client =           client
        self.model_name =       model_name
        self.max_retries =      max_retries
        self.batch_size =       batch_size
        self.wait_min =         wait_min
        self.wait_max =         wait_max
        self.wait_multiplier =  wait_multiplier
        self.tokenizer =        tiktoken.encoding_for_model(model_name)

    def _validate_text(self, text: str) -> None:
        """Validate input text for embedding generation."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        token_count = len(self.tokenizer.encode(text))
        if token_count > settings.OPENAI_EMBEDDING_MAX_TOKENS:
            raise ValueError(f"Text exceeds maximum token limit of {settings.OPENAI_EMBEDDING_MAX_TOKENS} tokens")

    async def create_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI API with retries."""
        self._validate_text(text)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=self.wait_multiplier,
                min=self.wait_min,
                max=self.wait_max
            ),
            reraise=True
        ):
            with attempt:
                try:
                    response = await self.client.embeddings.create(
                        model=self.model_name,
                        input=text
                    )
                    return response.data[0].embedding
                except Exception as e:
                    logger.error(f"Error creating embedding: {str(e)}")
                    raise

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI API with batching."""
        if not texts:
            return []

        for text in texts:
            self._validate_text(text)

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(
                    multiplier=self.wait_multiplier,
                    min=self.wait_min,
                    max=self.wait_max
                ),
                reraise=True
            ):
                with attempt:
                    try:
                        response = await self.client.embeddings.create(
                            model=self.model_name,
                            input=batch
                        )
                        batch_embeddings = [item.embedding for item in response.data]
                        all_embeddings.extend(batch_embeddings)
                    except Exception as e:
                        logger.error(f"Error creating embeddings for batch {i}: {str(e)}")
                        raise

        return all_embeddings

    async def get_embedding_dimensions(self) -> int:
        """Get the dimensionality of the embeddings for the current model."""
        test_embedding = await self.create_embedding("test")
        return len(test_embedding)
    