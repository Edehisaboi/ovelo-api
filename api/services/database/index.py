from typing import List

from pymongo import ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError, OperationFailure
from pymongo.operations import IndexModel
from langchain_mongodb.index import create_fulltext_search_index
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from config import get_logger, settings

logger = get_logger(__name__)


class MongoIndex:
    """
    A class to manage MongoDB vector and full-text search indexes using LangChain.
    Handles both movie and TV show collections with appropriate indexes for each.

    Attributes:
        retriever: An object responsible for vector store operations.
        collection: The MongoDB collection to create indexes on.
        collection_type: Type of collection ('movie' or 'tv').
    """

    def __init__(
            self,
            retriever:      MongoDBAtlasHybridSearchRetriever,
            collection:     Collection,
            collection_type: str
    ) -> None:
        """
        Initialize the MongoIndex instance.

        Args:
            retriever: The retriever object that manages the vector store.
            collection: The MongoDB collection to create indexes on.
            collection_type: Type of collection ('movie' or 'tv').

        Raises:
            ValueError: If collection_type is invalid.
        """
        self.retriever = retriever
        self.collection = collection
        self.collection_type = collection_type.lower()

        if self.collection_type not in [settings.MOVIES_COLLECTION, settings.TV_COLLECTION]:
            raise ValueError(
                f"collection_type must be either '{settings.MOVIES_COLLECTION}' or '{settings.TV_COLLECTION}'"
            )

    def _get_traditional_indexes(self) -> List[IndexModel]:
        """
        Get the traditional indexes based on collection type.

        Returns:
            List[IndexModel]: List of index models to create.
        """
        common_indexes = [
            IndexModel([("tmdb_id", ASCENDING)], unique=True),
            IndexModel([("external_ids.imdb_id", ASCENDING)], unique=True, sparse=True),
            IndexModel([("genres", ASCENDING)], name=f"{self.collection_type}_genres"),
            IndexModel([("spoken_languages.name", ASCENDING)], name=f"{self.collection_type}_languages"),
            IndexModel([("origin_country", ASCENDING)], name=f"{self.collection_type}_countries"),
            IndexModel([("cast.name", ASCENDING)], name=f"{self.collection_type}_cast"),
            IndexModel([("crew.name", ASCENDING)], name=f"{self.collection_type}_crew"),
            IndexModel([("watch_providers.flatrate.provider_name", ASCENDING)],
                       name=f"{self.collection_type}_providers")
        ]

        if self.collection_type == settings.MOVIES_COLLECTION:
            return common_indexes + [
                IndexModel([
                    ("title", TEXT),
                    ("original_title", TEXT),
                    ("tagline", TEXT)
                ], name="movie_text_search"),
                IndexModel([
                    ("status", ASCENDING),
                    ("release_date", ASCENDING)
                ], name="movie_status_date")
            ]
        else:
            return common_indexes + [
                IndexModel([
                    ("name", TEXT),
                    ("original_name", TEXT),
                    ("tagline", TEXT)
                ], name="tv_text_search"),
                IndexModel([
                    ("status", ASCENDING),
                    ("first_air_date", ASCENDING)
                ], name="tv_status_date"),
                IndexModel([("seasons.season_number", ASCENDING)], name="tv_seasons"),
                IndexModel([
                    ("seasons.episodes.episode_number", ASCENDING),
                    ("seasons.season_number", ASCENDING)
                ], name="tv_episodes")
            ]

    def _index_exists(self, index_name: str) -> bool:
        """
        Check if an index with the given name exists in the collection.

        Args:
            index_name: The name of the index to check.

        Returns:
            bool: True if the index exists, False otherwise.
        """
        try:
            existing_indexes = self.collection.index_information()
            return index_name in existing_indexes
        except PyMongoError as e:
            logger.error(f"Error checking index existence for '{index_name}': {e}")
            return False

    def _create_vector_index(self, embedding_dim: int) -> bool:
        """
        Create a vector search index for the collection.

        Args:
            embedding_dim: The dimensionality of the vector embeddings.

        Returns:
            bool: True if the index was created, False if it already exists.

        Raises:
            ValueError: If embedding_dim is invalid.
            PyMongoError: If index creation fails.
        """
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be a positive integer")

        vector_index_name = self.retriever.vectorstore.index_name
        if self._index_exists(vector_index_name):
            logger.info(
                f"Vector search index '{vector_index_name}' already exists for {self.collection_type} collection")
            return False

        try:
            self.retriever.vectorstore.create_vector_search_index(dimensions=embedding_dim)
            logger.info(f"Created vector search index '{vector_index_name}' for {self.collection_type} collection")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to create vector search index: {e}")
            raise

    def _create_traditional_indexes(self) -> int:
        """
        Create traditional indexes for the collection.

        Returns:
            int: Number of indexes created.

        Raises:
            PyMongoError: If index creation fails.
        """
        created_count = 0
        traditional_indexes = self._get_traditional_indexes()

        for index in traditional_indexes:
            index_name = index.document.get("name")
            if index_name and self._index_exists(index_name):
                logger.info(f"Traditional index '{index_name}' already exists for {self.collection_type} collection")
                continue

            try:
                self.collection.create_indexes([index])
                logger.info(f"Created traditional index '{index_name}' for {self.collection_type} collection")
                created_count += 1
            except (DuplicateKeyError, OperationFailure) as e:
                logger.warning(f"Skipping creation of index '{index_name}' due to: {e}")
            except PyMongoError as e:
                logger.error(f"Failed to create traditional index '{index_name}': {e}")
                raise

        return created_count

    def _create_fulltext_index(self, text_field: str, index_name: str) -> bool:
        """
        Create a full-text search index for the collection.

        Args:
            text_field: The field to use for full-text search indexing.
            index_name: The name of the full-text search index.

        Returns:
            bool: True if the index was created, False if it already exists.

        Raises:
            PyMongoError: If index creation fails.
        """
        if self._index_exists(index_name):
            logger.info(f"Full-text search index '{index_name}' already exists for {self.collection_type} collection")
            return False

        try:
            create_fulltext_search_index(
                collection=self.collection,
                field=text_field,
                index_name=index_name
            )
            logger.info(f"Created full-text search index '{index_name}' for {self.collection_type} collection")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to create full-text search index '{index_name}': {e}")
            raise

    async def create(
            self,
            embedding_dim: int,
            index_name: str,
            text_field: str,
            is_hybrid: bool = False
    ) -> None:
        """
        Create vector search, traditional, and optional full-text indexes for the collection.

        Args:
            embedding_dim: The dimensionality of the vector embeddings.
            index_name: The name of the full-text search index.
            text_field: The field to use for full-text search indexing.
            is_hybrid: Whether to create a full-text search index in addition to the vector index.

        Raises:
            ValueError: If embedding_dim is invalid or MongoDB collection is not initialized.
            PyMongoError: If index creation fails.
            Exception: For unexpected errors during index creation.
        """
        try:
            if not self.collection:
                raise ValueError("MongoDB collection is not initialized")

            # Create vector search index
            vector_created = self._create_vector_index(embedding_dim=embedding_dim)

            # Create traditional indexes
            traditional_created = self._create_traditional_indexes()

            # Create full-text search index if hybrid search is enabled
            fulltext_created = False
            if is_hybrid:
                fulltext_created = self._create_fulltext_index(
                    text_field=text_field,
                    index_name=index_name
                )

            # Log overall result
            created_types = []
            if vector_created:
                created_types.append("vector")
            if traditional_created > 0:
                created_types.append(f"{traditional_created} traditional")
            if fulltext_created:
                created_types.append("full-text")

            if created_types:
                logger.info(f"Created {', '.join(created_types)} indexes for {self.collection_type} collection")
            else:
                logger.info(
                    f"No new indexes created for {self.collection_type} collection; all specified indexes already exist")

        except (ValueError, PyMongoError) as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during index creation: {e}")
            raise