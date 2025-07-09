from typing import Generic, Type, TypeVar

from bson import ObjectId
from pydantic import BaseModel
from pymongo import MongoClient, errors
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from .indexes import MongoIndex
from application.core.config import settings
from application.core.logging import get_logger
from external.clients import get_embedding_client
from application.repositories.document import movie_document, tv_document
from application.models.media import MovieDetails, TVDetails

logger = get_logger(__name__)
T      = TypeVar("T", bound=BaseModel)


class MongoClientWrapper(Generic[T]):
    """Service class for MongoDB operations, supporting ingestion, querying, and validation.

    This class provides methods to interact with MongoDB collections, including document
    ingestion, querying, and validation operations.

    Args:
        model (Type[T]): The Pydantic model class to use for document serialization.
        collection_name (str): Name of the MongoDB collection to use.
        database_name (str, optional): Name of the MongoDB database to use.
        mongodb_uri (str, optional): URI for connecting to a MongoDB instance.

    Attributes:
        model (Type[T]): The Pydantic model class used for document serialization.
        collection_name (str): Name of the MongoDB collection.
        database_name (str): Name of the MongoDB database.
        mongodb_uri (str): MongoDB connection URI.
        client (MongoClient): MongoDB client instance for database connections.
        database (Database): Reference to the target MongoDB database.
        retriever (Optional[MongoDBAtlasHybridSearchRetriever]): Hybrid search retriever instance.
    """

    def __init__(
        self,
        model:           Type[T],
        collection_name: str,
        database_name:   str = settings.MONGODB_DB,
        mongodb_uri:     str = settings.MONGODB_URL,
    ) -> None:
        """Initialize a connection to the MongoDB collection.

        Args:
            model (Type[T]): The Pydantic model class to use for document serialization.
            collection_name (str): Name of the MongoDB collection to use.
            database_name (str, optional): Name of the MongoDB database to use.
                Defaults to value from settings.
            mongodb_uri (str, optional): URI for connecting to MongoDB instance.
                Defaults to value from settings.

        Raises:
            Exception: If connection to MongoDB fails.
        """
        self.model           = model
        self.collection_name = collection_name
        self.database_name   = database_name
        self.mongodb_uri     = mongodb_uri
        self.retriever       = None
        self._is_closed      = False

        try:
            self.client = MongoClient(
                mongodb_uri, 
                appname="moovzmatch",
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Test the connection
            self.client.admin.command("ping")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {e}")
            raise

        self.database   = self.client[database_name]
        self.collection = self.database[collection_name]
        logger.info(
            f"Connected to MongoDB instance:\n Database: {database_name}\n Collection: {collection_name}"
        )

    def __enter__(self) -> "MongoClientWrapper":
        """Enable context manager support.

        Returns:
            MongoClientWrapper: The current instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close MongoDB connection when exiting context.

        Args:
            exc_type: Type of exception that occurred, if any.
            exc_val: Exception instance that occurred, if any.
            exc_tb: Traceback of exception that occurred, if any.
        """
        self.close()

    def initialize_indexes(self) -> None:
        """Initialize indexes for the collection.

        This method creates both vector search and traditional indexes for the collection.
        It also initializes the hybrid search retriever if not already initialized.
        """
        try:
            # Get collection-specific settings
            if self.collection_name == settings.MOVIES_COLLECTION:
                embedding_dim     = settings.MOVIE_NUM_DIMENSIONS
                index_name        = settings.MOVIE_INDEX_NAME
                text_path         = settings.MOVIE_TEXT_PATH
                embedding_path    = settings.MOVIE_EMBEDDING_PATH
                similarity_metric = settings.MOVIE_SIMILARITY
            else:
                embedding_dim     = settings.TV_NUM_DIMENSIONS
                index_name        = settings.TV_INDEX_NAME
                text_path         = settings.TV_TEXT_PATH
                embedding_path    = settings.TV_EMBEDDING_PATH
                similarity_metric = settings.TV_SIMILARITY

            # Initialize the retriever if not already done
            if not self.retriever:
                self.retriever = self._get_hybrid_search_retriever(
                    text_key          = text_path,
                    embedding_key     = embedding_path,
                    index_name        = index_name,
                    similarity_metric = similarity_metric
                )

            # Create indexes
            index = MongoIndex(
                retriever       = self.retriever,
                collection      = self.collection,
                collection_type = self.collection_name
            )
            index.create(
                embedding_dim = embedding_dim,
                index_name    = index_name,
                text_field    = text_path,
                is_hybrid     = True
            )
        except Exception as e:
            logger.error(f"Error initializing indexes: {e}")
            raise

    def clear_collection(self) -> None:
        """Remove all documents from the collection.

        This method deletes all documents in the collection.

        Raises:
            errors.PyMongoError: If the deletion operation fails.
        """
        try:
            result = self.collection.delete_many({})
            logger.debug(
                f"Cleared collection. Deleted {result.deleted_count} documents."
            )
        except errors.PyMongoError as e:
            logger.error(f"Error clearing the collection: {e}")
            raise

    def ingest_document(self, document: T) -> str:
        """Insert a single document into the MongoDB collection.

        Args:
            document: Pydantic model instance to insert.

        Returns:
            str: The ID of the inserted document.

        Raises:
            ValueError: If document is not a Pydantic model instance.
            errors.PyMongoError: If the insertion operation fails.
        """
        try:
            if not isinstance(document, BaseModel):
                raise ValueError("Document must be a Pydantic model instance.")

            # Use appropriate document builder based on collection
            if self.collection_name == settings.MOVIES_COLLECTION:
                if isinstance(document, MovieDetails):
                    doc_dict = movie_document.build(document)
                else:
                    doc_dict = document.model_dump()
            elif self.collection_name == settings.TV_COLLECTION:
                if isinstance(document, TVDetails):
                    doc_dict = tv_document.build(document)
                else:
                    doc_dict = document.model_dump()
            else:
                doc_dict = document.model_dump()

            result      = self.collection.insert_one(doc_dict)
            document_id = str(result.inserted_id)

            logger.debug(f"Inserted document with ID: {document_id}")
            return document_id
        except errors.PyMongoError as e:
            logger.error(f"Error inserting document: {e}")
            raise

    def update_document(self, document_id: str, document: T) -> bool:
        """Update a document in the MongoDB collection.

        Args:
            document_id: The ID of the document to update.
            document: Pydantic model instance with updated data.

        Returns:
            bool: True if the document was updated, False otherwise.

        Raises:
            ValueError: If document is not a Pydantic model instance.
            errors.PyMongoError: If the update operation fails.
        """
        try:
            if not isinstance(document, BaseModel):
                raise ValueError("Document must be a Pydantic model instance.")

            # Use appropriate document builder based on collection
            if self.collection_name == settings.MOVIES_COLLECTION:
                if isinstance(document, MovieDetails):
                    doc_dict = movie_document.build(document)
                else:
                    doc_dict = document.model_dump()
            elif self.collection_name == settings.TV_COLLECTION:
                if isinstance(document, TVDetails):
                    doc_dict = tv_document.build(document)
                else:
                    doc_dict = document.model_dump()
            else:
                doc_dict = document.model_dump()

            result = self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": doc_dict}
            )

            success = result.modified_count > 0
            if success:
                logger.debug(f"Updated document with ID: {document_id}")
            else:
                logger.warning(f"No document found with ID: {document_id}")

            return success
        except errors.PyMongoError as e:
            logger.error(f"Error updating document: {e}")
            raise

    def get_collection_count(self) -> int:
        """Count the total number of documents in the collection.

        Returns:
            int: Total number of documents in the collection.

        Raises:
            errors.PyMongoError: If the count operation fails.
        """
        try:
            return self.collection.count_documents({})
        except errors.PyMongoError as e:
            logger.error(f"Error counting documents in MongoDB: {e}")
            raise

    def _get_hybrid_search_retriever(
        self,
        text_key:          str,
        embedding_key:     str,
        index_name:        str,
        similarity_metric: str,
        k:                 int = settings.RAG_TOP_K
    ) -> MongoDBAtlasHybridSearchRetriever:
        """Get a hybrid search retriever for this collection.

        Args:
            text_key (str): Field to use for text search.
            embedding_key (str): Field to use for vector search.
            index_name (str): Name of the search index to use.
            similarity_metric (str): Similarity metric to use for vector search.
            k (int, optional): Number of documents to retrieve. Defaults to settings.RAG_TOP_K.

        Returns:
            MongoDBAtlasHybridSearchRetriever: A configured hybrid search retriever.
        """
        vectorstore = MongoDBAtlasVectorSearch.from_connection_string(
            connection_string  = self.mongodb_uri,
            embedding          = get_embedding_client().embeddings,
            namespace          = f"{self.database_name}.{self.collection_name}",
            text_key           = text_key,
            embedding_key      = embedding_key,
            relevance_score_fn = similarity_metric,
        )

        return MongoDBAtlasHybridSearchRetriever(
            vectorstore       = vectorstore,
            search_index_name = index_name,
            top_k             = k,
            vector_penalty    = settings.VECTOR_PENALTY,
            fulltext_penalty  = settings.FULLTEXT_PENALTY
        )

    def close(self) -> None:
        """Close the MongoDB connection.

        This method should be called when the service is no longer needed
        to properly release resources, unless using the context manager.
        """
        if not self._is_closed:
            try:
                self.client.close()
                self._is_closed = True
                logger.debug("Closed MongoDB connection.")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
    
    def is_connected(self) -> bool:
        """Check if the MongoDB connection is still active.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        if self._is_closed:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False 