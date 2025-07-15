from typing import List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, TEXT, IndexModel
from pymongo.errors import OperationFailure

from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


class MongoIndex:
    """Utility class for managing both traditional and vector indexes on a MongoDB collection.
    On each (re)build, ALL indexes are dropped and then freshly created."""

    def __init__(
        self,
        retriever: MongoDBAtlasHybridSearchRetriever,
        collection: AsyncIOMotorCollection,
        collection_type: str
    ):
        self.retriever = retriever
        self.collection = collection
        self.collection_type = collection_type

    async def create_indexes(self) -> None:
        """Drops all existing indexes and recreates required indexes for this collection.
        This ensures the index state is always as defined here."""
        try:
            # Drop all indexes first
            await self.drop_all_indexes()

            # Define new indexes
            indexes = [
                IndexModel([("tmdb_id", ASCENDING)], unique=True, name="tmdbid"),
                IndexModel([("genres.name", ASCENDING)], name="genre"),
                IndexModel([("original_language", ASCENDING)], name="language"),
                IndexModel([("spoken_languages.name", ASCENDING)], name="languages"),
                IndexModel([("origin_country", ASCENDING)], name="country"),
            ]
            if self.collection_type == settings.MOVIES_COLLECTION:
                indexes.append(
                    IndexModel([("title", TEXT), ("original_title", TEXT)], name="titletext")
                )
            elif self.collection_type == settings.TV_COLLECTION:
                indexes.append(
                    IndexModel([("name", TEXT), ("original_name", TEXT)], name="nametext")
                )

            # Create all indexes at once
            await self.collection.create_indexes(indexes)
            logger.info(f"Created indexes: {[i.document['name'] for i in indexes]} for '{self.collection_type}'.")

        except OperationFailure as e:
            logger.error(f"MongoDB OperationFailure during index creation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during index creation: {e}")
            raise

    async def create_vector_indexes(self, embedding_dim: int, is_hybrid: bool = True) -> None:
        """Drops all existing indexes and creates the vector search index using the retriever's vectorstore."""
        try:
            # Drop all indexes before creating the vector index
            await self.drop_all_indexes()

            vectorstore = self.retriever.vectorstore
            if not vectorstore:
                raise ValueError("Vectorstore is not initialized.")

            vectorstore.create_vector_search_index(dimensions=embedding_dim)
            logger.info(f"Created vector search index for '{self.collection_type}'.")

        except OperationFailure as e:
            logger.error(f"MongoDB OperationFailure during vector index creation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during vector index creation: {e}")
            raise

    async def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes on the collection."""
        try:
            indexes = []
            async for index in self.collection.list_indexes():
                indexes.append(dict(index))
            logger.debug(f"Listed {len(indexes)} indexes for '{self.collection_type}'.")
            return indexes
        except Exception as e:
            logger.error(f"Error listing indexes: {e}")
            raise

    async def drop_index(self, index_name: str) -> None:
        """Drop a specific index by name."""
        try:
            await self.collection.drop_index(index_name)
            logger.info(f"Dropped index '{index_name}' from '{self.collection_type}'.")
        except Exception as e:
            logger.error(f"Error dropping index '{index_name}': {e}")
            raise

    async def drop_all_indexes(self) -> None:
        """Drop all indexes from the collection."""
        try:
            await self.collection.drop_indexes()
            logger.info(f"Dropped all indexes from '{self.collection_type}'.")
        except Exception as e:
            logger.error(f"Error dropping all indexes: {e}")
            raise
