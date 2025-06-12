from langchain_openai import OpenAIEmbeddings

from config import settings


class EmbeddingClient:
    """OpenAI embedding client implementation with retries and error handling."""
    def __init__(
        self,
        model_name: str = settings.OPENAI_EMBEDDING_MODEL
    ):
        self.model_name = model_name

    @property
    def get_openai_embedding_model(
        self
    ) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            model=self.model_name,
            openai_api_key=settings.OPENAI_API_KEY,
            chunk_size=settings.CHUNK_SIZE,
            max_retries=settings.OPENAI_EMBEDDING_MAX_RETRIES,
            retry_min_seconds=settings.OPENAI_EMBEDDING_WAIT_MIN,
            retry_max_seconds=settings.OPENAI_EMBEDDING_WAIT_MAX,
            request_timeout=settings.OPENAI_EMBEDDING_TIMEOUT
        )
    