from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, TEXT, IndexModel
from pymongo.errors import OperationFailure

from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


class MongoIndex:
    """
    Service for managing MongoDB indexes and vector/hybrid search configurations.
    """
    def __init__(
        self,
        retriever: MongoDBAtlasHybridSearchRetriever,
        collection: AsyncIOMotorCollection,
        collection_type: str
    ):
        """
        Args:
            retriever: Hybrid search retriever instance.
            collection: MongoDB collection instance.
            collection_type: Name/type of collection (e.g., 'movies', 'tv_shows').
        """
        self.retriever = retriever
        self.collection = collection
        self.collection_type = collection_type

    async def create_traditional_indexes(self) -> None:
        """
        Create traditional MongoDB indexes for efficient querying and search,
        skipping creation if indexes already exist.
        """
        try:
            existing_indexes = await self.list_indexes()
            index_names = [idx.get("name") for idx in existing_indexes]

            # Only create if 'tmdb_id_unique' does not exist
            if "tmdb_id_unique" in index_names:
                logger.info(f"Traditional indexes already exist for '{self.collection_type}', skipping creation.")
                return

            indexes = [
                IndexModel([("tmdb_id", ASCENDING)], unique=True, name="tmdb_id_unique"),
                IndexModel([("genres.name", ASCENDING)], name="genres_index"),
                IndexModel([("spoken_languages.name", ASCENDING)], name="languages_index"),
                IndexModel([("origin_country", ASCENDING)], name="country_index"),
            ]

            if self.collection_type == settings.MOVIES_COLLECTION:
                indexes.append(IndexModel(
                    [("title", TEXT), ("original_title", TEXT)], name="title_search_index"
                ))
            elif self.collection_type == settings.TV_COLLECTION:
                indexes.append(IndexModel(
                    [("name", TEXT), ("original_name", TEXT)], name="title_name_search_index"
                ))
                indexes.append(IndexModel(
                    [("number_of_seasons", ASCENDING)], name="seasons_index"
                ))

            # Drop existing text indexes to avoid conflicts
            try:
                async for index in self.collection.list_indexes():
                    if index.get("key", {}).get("_fts") == "text":
                        await self.collection.drop_index(index["name"])
            except Exception as e:
                logger.warning(f"Error dropping existing text indexes: {e}")

            try:
                await self.collection.create_indexes(indexes)
                logger.debug(f"Created traditional indexes for '{self.collection_type}' collection.")
            except OperationFailure as e:
                if "already exists" in str(e) or "IndexAlreadyExists" in str(e):
                    logger.info(f"Traditional indexes already exist for '{self.collection_type}', skipping creation.")
                else:
                    raise

        except OperationFailure as e:
            logger.error(f"Error creating traditional indexes: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating traditional indexes: {e}")
            raise

    async def create_vector_search_indexes(self, embedding_dim: int, is_hybrid: bool = True) -> None:
        """
        Create vector (semantic) search and hybrid indexes.
        """
        try:
            # List current indexes and check for vector index by name
            existing_indexes = await self.list_indexes()
            vector_index_exists = any(
                idx.get("name", "").lower().startswith("vector")
                or "vector" in idx.get("name", "").lower()
                for idx in existing_indexes
            )

            if vector_index_exists:
                logger.info(f"Vector search index already exists for '{self.collection_type}', skipping creation.")
                return

            vectorstore = self.retriever.vectorstore
            if not vectorstore:
                raise ValueError("Vectorstore is not initialized.")

            try:
                vectorstore.create_vector_search_index(dimensions=embedding_dim)
                logger.debug(f"Created vector search index for '{self.collection_type}'.")
            except OperationFailure as e:
                if "already defined" in str(e) or "IndexAlreadyExists" in str(e):
                    logger.info(f"Vector search index already exists for '{self.collection_type}', skipping creation.")
                else:
                    raise

            logger.debug(f"Vector/hybrid search indexes ready for '{self.collection_type}'.")

        except OperationFailure as e:
            logger.error(f"Error creating vector search index: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating vector search index: {e}")
            raise

    async def list_indexes(self) -> List[Dict[str, Any]]:
        """
        List all indexes for the collection.
        Returns:
            List of index info dicts.
        """
        try:
            indexes = []
            async for index in self.collection.list_indexes():
                indexes.append(dict(index))
            logger.debug(f"Found {len(indexes)} indexes for '{self.collection_type}'.")
            return indexes
        except Exception as e:
            logger.error(f"Error listing indexes: {e}")
            raise

    async def drop_index(self, index_name: str) -> None:
        """
        Drop a specific index by name.
        Args:
            index_name: Name of the index to drop.
        """
        try:
            await self.collection.drop_index(index_name)
            logger.info(f"Dropped index '{index_name}' from '{self.collection_type}'.")
        except Exception as e:
            logger.error(f"Error dropping index '{index_name}': {e}")
            raise

    async def drop_all_indexes(self) -> None:
        """
        Drop all indexes except the default _id index.
        """
        try:
            await self.collection.drop_indexes()
            logger.info(f"Dropped all indexes from '{self.collection_type}'.")
        except Exception as e:
            logger.error(f"Error dropping all indexes: {e}")
            raise
