from typing import List, Dict, Any

from pymongo import ASCENDING, TEXT, IndexModel
from pymongo.errors import OperationFailure
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


class MongoIndex:
    """Service for managing MongoDB indexes and vector search configurations."""

    def __init__(
        self,
        retriever: MongoDBAtlasHybridSearchRetriever,
        collection,
        collection_type: str
    ):
        """Initialize the index manager.

        Args:
            retriever: Hybrid search retriever instance.
            collection: MongoDB collection instance.
            collection_type: Type of collection (movies or tv_shows).
        """
        self.retriever = retriever
        self.collection = collection
        self.collection_type = collection_type

    def create(
        self,
        embedding_dim: int,
        index_name: str,
        text_field: str,
        is_hybrid: bool = True
    ) -> None:
        """Create indexes for the collection.

        Args:
            embedding_dim: Dimension of the embedding vectors.
            index_name: Name of the search index.
            text_field: Field to use for text search.
            is_hybrid: Whether to create hybrid search indexes.
        """
        try:
            # Create traditional indexes
            self._create_traditional_indexes()

            # Vector search index creation is skipped (Atlas only)
            # if is_hybrid:
            #     self._create_vector_search_indexes(
            #         embedding_dim=embedding_dim,
            #         index_name=index_name,
            #         text_field=text_field
            #     )

            logger.info(f"Successfully created indexes for {self.collection_type} collection")

        except Exception as e:
            logger.error(f"Error creating indexes for {self.collection_type}: {e}")
            raise

    def _create_traditional_indexes(self) -> None:
        """Create traditional MongoDB indexes for efficient querying."""
        try:
            # Text index for full-text search
            text_index = IndexModel([("title", TEXT), ("overview", TEXT)], name="text_search")
            
            # Single field indexes for common queries
            indexes = [
                IndexModel([("tmdb_id", ASCENDING)], unique=True, name="tmdb_id_unique"),
                IndexModel([("title", ASCENDING)], name="title_index"),
                IndexModel([("release_date", ASCENDING)], name="release_date_index"),
                IndexModel([("vote_average", ASCENDING)], name="vote_average_index"),
                IndexModel([("vote_count", ASCENDING)], name="vote_count_index"),
                IndexModel([("status", ASCENDING)], name="status_index"),
                IndexModel([("genres.name", ASCENDING)], name="genres_index"),
                IndexModel([("spoken_languages.name", ASCENDING)], name="languages_index"),
                IndexModel([("origin_country", ASCENDING)], name="country_index"),
                text_index
            ]

            # Add TV-specific indexes
            if self.collection_type == settings.TV_COLLECTION:
                tv_indexes = [
                    IndexModel([("name", ASCENDING)], name="name_index"),
                    IndexModel([("first_air_date", ASCENDING)], name="first_air_date_index"),
                    IndexModel([("last_air_date", ASCENDING)], name="last_air_date_index"),
                    IndexModel([("number_of_seasons", ASCENDING)], name="seasons_index"),
                    IndexModel([("number_of_episodes", ASCENDING)], name="episodes_index"),
                ]
                indexes.extend(tv_indexes)

            # Create indexes
            self.collection.create_indexes(indexes)
            logger.debug(f"Created traditional indexes for {self.collection_type}")

        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info(f"Traditional indexes already exist for {self.collection_type}")
            else:
                logger.error(f"Error creating traditional indexes: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating traditional indexes: {e}")
            raise

    def _create_vector_search_indexes(
        self,
        embedding_dim: int,
        index_name: str,
        text_field: str
    ) -> None:
        """Create vector search indexes for semantic search."""
        try:
            # Define the search index configuration
            search_index_definition = {
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        "embedding": {
                            "dimensions": embedding_dim,
                            "similarity": "cosine",
                            "type": "knnVector"
                        },
                        text_field: {
                            "type": "string"
                        }
                    }
                }
            }

            # Create the search index
            self.collection.create_search_index(
                definition=search_index_definition,
                name=index_name
            )
            logger.debug(f"Created vector search index '{index_name}' for {self.collection_type}")

        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info(f"Vector search index '{index_name}' already exists for {self.collection_type}")
            else:
                logger.error(f"Error creating vector search index: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating vector search index: {e}")
            raise

    def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes for the collection.

        Returns:
            List[Dict[str, Any]]: List of index information.
        """
        try:
            indexes = list(self.collection.list_indexes())
            logger.debug(f"Found {len(indexes)} indexes for {self.collection_type}")
            return indexes
        except Exception as e:
            logger.error(f"Error listing indexes: {e}")
            raise

    def drop_index(self, index_name: str) -> None:
        """Drop a specific index.

        Args:
            index_name: Name of the index to drop.
        """
        try:
            self.collection.drop_index(index_name)
            logger.info(f"Dropped index '{index_name}' from {self.collection_type}")
        except Exception as e:
            logger.error(f"Error dropping index '{index_name}': {e}")
            raise

    def drop_all_indexes(self) -> None:
        """Drop all indexes except the default _id index."""
        try:
            self.collection.drop_indexes()
            logger.info(f"Dropped all indexes from {self.collection_type}")
        except Exception as e:
            logger.error(f"Error dropping all indexes: {e}")
            raise 