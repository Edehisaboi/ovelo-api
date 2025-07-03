from langchain_openai import OpenAIEmbeddings

from config import settings


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
    