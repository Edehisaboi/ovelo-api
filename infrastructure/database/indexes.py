from typing import List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, TEXT, IndexModel
from pymongo.errors import OperationFailure

#from langchain_mongodb.index import create_fulltext_search_index
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


class MongoIndex:
    """Service for managing MongoDB indexes and vector search configurations."""

    def __init__(
        self,
        retriever: MongoDBAtlasHybridSearchRetriever,
        collection: AsyncIOMotorCollection,
        collection_type: str
    ):
        """
        Initialize the index manager.

        Args:
            retriever: Hybrid search retriever instance.
            collection: MongoDB collection instance.
            collection_type: Type of collection (e.g., movies, tv_shows).
        """
        self.retriever = retriever
        self.collection = collection
        self.collection_type = collection_type

    async def create(
        self,
        embedding_dim: int,
        is_hybrid: bool = True
    ) -> None:
        """
        Create all relevant indexes for the collection.

        Args:
            embedding_dim: Dimension of the embedding vectors.
            is_hybrid: Whether to create hybrid search indexes.
        """
        try:
            await self._create_traditional_indexes()
            await self._create_vector_search_indexes(embedding_dim, is_hybrid)
            logger.info(f"Successfully created indexes for '{self.collection_type}' collection.")
        except Exception as e:
            logger.error(f"Error creating indexes for '{self.collection_type}': {e}")
            raise

    async def _create_traditional_indexes(self) -> None:
        """
        Create traditional MongoDB indexes for efficient querying and search.
        """
        try:
            indexes = [
                IndexModel([("tmdb_id", ASCENDING)], unique=True, name="tmdb_id_unique"),
                IndexModel([("genres.name", ASCENDING)], name="genres_index"),
                IndexModel([("spoken_languages.name", ASCENDING)], name="languages_index"),
                IndexModel([("origin_country", ASCENDING)], name="country_index"),
            ]

            if self.collection_type == settings.MOVIES_COLLECTION:
                # MovieDetails: text index on 'title' and 'original_title'
                indexes.append(IndexModel([("title", TEXT), ("original_title", TEXT)], name="title_search_index"))
            elif self.collection_type == settings.TV_COLLECTION:
                # TVDetails: compound text index on 'name' and 'original_name'
                indexes.append(IndexModel([("name", TEXT), ("original_name", TEXT)], name="title_name_search_index"))
                indexes.append(IndexModel([("number_of_seasons", ASCENDING)], name="seasons_index"))

            # Drop existing text indexes to avoid conflicts
            async for index in self.collection.list_indexes():
                if index.get("key", {}).get("_fts") == "text":
                    await self.collection.drop_index(index["name"])

            # Create (or recreate) all indexes
            await self.collection.create_indexes(indexes)
            logger.debug(f"Created traditional indexes for '{self.collection_type}' collection.")

        except OperationFailure as e:
            logger.error(f"Error creating traditional indexes: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating traditional indexes: {e}")
            raise

    async def _create_vector_search_indexes(
        self,
        embedding_dim: int,
        is_hybrid: bool = True
    ) -> None:
        """
        Create vector search (semantic search) and hybrid indexes.
        """
        try:
            vectorstore = self.retriever.vectorstore
            if not vectorstore:
                raise ValueError("Vectorstore is not initialized.")
            vectorstore.create_vector_search_index(dimensions=embedding_dim)

            # if is_hybrid:
            #     create_fulltext_search_index(
            #         collection=self.collection,
            #         index_name=self.retriever.search_index_name,
            #         field=vectorstore._text_key
            #     )
            #     # Note: create_fulltext_search_index expects sync collection
            #     # We'll need to handle this differently or use a sync wrapper
            logger.debug(f"Created vector/hybrid search indexes for '{self.collection_type}'.")

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
            A list of index information dicts.
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
            index_name: The name of the index to drop.
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
