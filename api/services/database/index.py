from typing import List

from pymongo import ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from pymongo.operations import IndexModel
from langchain_mongodb.index import create_fulltext_search_index
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from config import get_logger

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
        retriever: MongoDBAtlasHybridSearchRetriever,
        collection: Collection,
        collection_type: str
    ) -> None:
        """
        Initialize the MongoIndex instance.

        Args:
            retriever: The retriever object that manages the vector store.
            collection: The MongoDB collection to create indexes on.
            collection_type: Type of collection ('movie' or 'tv').
        """
        self.retriever = retriever
        self.collection = collection
        self.collection_type = collection_type.lower()
        if self.collection_type not in ['movie', 'tv']:
            raise ValueError("collection_type must be either 'movie' or 'tv'")

    def _get_traditional_indexes(self) -> List[IndexModel]:
        """
        Get the traditional indexes based on collection type.

        Returns:
            List[IndexModel]: List of index models to create.
        """
        common_indexes = [
            # Unique indexes for identifiers
            IndexModel([("tmdb_id", ASCENDING)], unique=True),
            IndexModel([("external_ids.imdb_id", ASCENDING)], unique=True, sparse=True),
            
            # Array indexes for filtering
            IndexModel([("genres", ASCENDING)], name=f"{self.collection_type}_genres"),
            IndexModel([("spoken_languages.name", ASCENDING)], name=f"{self.collection_type}_languages"),
            IndexModel([("origin_country", ASCENDING)], name=f"{self.collection_type}_countries"),
            
            # Cast and crew indexes
            IndexModel([("cast.name", ASCENDING)], name=f"{self.collection_type}_cast"),
            IndexModel([("crew.name", ASCENDING)], name=f"{self.collection_type}_crew"),
            
            # Watch provider indexes
            IndexModel([("watch_providers.flatrate.provider_name", ASCENDING)], name=f"{self.collection_type}_providers")
        ]

        if self.collection_type == 'movie':
            return common_indexes + [
                # Text indexes for searchable fields
                IndexModel([
                    ("title", TEXT),
                    ("original_title", TEXT),
                    ("tagline", TEXT)
                ], name="movie_text_search"),
                
                # Compound indexes for common query patterns
                IndexModel([
                    ("status", ASCENDING),
                    ("release_date", ASCENDING)
                ], name="movie_status_date")
            ]
        else:
            return common_indexes + [
                # Text indexes for searchable fields
                IndexModel([
                    ("name", TEXT),
                    ("original_name", TEXT),
                    ("tagline", TEXT)
                ], name="tv_text_search"),
                
                # Compound indexes for common query patterns
                IndexModel([
                    ("status", ASCENDING),
                    ("first_air_date", ASCENDING)
                ], name="tv_status_date"),
                
                # Season and episode indexes
                IndexModel([("seasons.season_number", ASCENDING)], name="tv_seasons"),
                IndexModel([
                    ("seasons.episodes.episode_number", ASCENDING),
                    ("seasons.season_number", ASCENDING)
                ], name="tv_episodes")
            ]

    async def create(
        self,
        embedding_dim:  int,
        index_name:     str,
        text_field:     str,
        is_hybrid:      bool = False,
    ) -> None:
        """
        Create vector search and traditional indexes for the collection.

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
            # Create vector search index using LangChain
            vectorstore = self.retriever.vectorstore
            vectorstore.create_vector_search_index(dimensions=embedding_dim)
            logger.info(f"Created vector search index for {self.collection_type} collection.")

            # Create traditional indexes
            traditional_indexes = self._get_traditional_indexes()
            self.collection.create_indexes(traditional_indexes)
            logger.info(f"Created {self.collection_type} traditional indexes successfully.")

            # Create full-text search index if hybrid search is enabled
            if is_hybrid:
                create_fulltext_search_index(
                    collection=self.collection,
                    field=text_field,
                    index_name=index_name,
                )
                logger.info(f"Created full-text search index '{index_name}' for {self.collection_type} collection.")

        except PyMongoError as e:
            raise PyMongoError(f"Failed to create index: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during index creation: {str(e)}")