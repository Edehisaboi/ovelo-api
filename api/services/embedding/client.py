from typing import List
from openai import OpenAI
from config import Settings


class EmbeddingClient:
    """OpenAI embedding client implementation."""
    
    def __init__(
            self,
            client: OpenAI,
            model_name: str = Settings.OPENAI_EMBEDDING_MODEL
        ):
        self.client = client
        self.model_name = model_name

    async def create_embedding(
            self,
            text: str
        ) -> List[float]:
        """Generate embedding for a single text using OpenAI API."""
        response = await self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return response.data[0].embedding

    async def create_embeddings(
            self,
            texts: List[str]
        ) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI API."""
        response = await self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [item.embedding for item in response.data] 