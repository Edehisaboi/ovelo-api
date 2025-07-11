from typing import Generic, Type, TypeVar, Optional

from bson import ObjectId
from pydantic import BaseModel

from pymongo import MongoClient, errors
from pymongo.collection import Collection

from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from external.clients import EmbeddingClient
from application.core.logging import get_logger
from application.models.media import MovieDetails, TVDetails
from application.repositories import movie_document, tv_document

from .indexes import MongoIndex

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class MongoClientWrapper(Generic[T]):
    """
    Service class for MongoDB operations, supporting ingestion, querying, and validation.
    """

    def __init__(
        self,
        model:           Type[T],
        collection_name: str,
        database_name:   str,
        mongodb_uri:     str,
        embedding_client: "EmbeddingClient" = None
    ) -> None:
        self.model           = model
        self.collection_name = collection_name
        self.database_name   = database_name
        self.mongodb_uri     = mongodb_uri
        self.embedding_client= embedding_client
        self.retriever       : Optional[MongoDBAtlasHybridSearchRetriever] = None
        self._is_closed      = False

        try:
            self.client = MongoClient(
                mongodb_uri,
                appname="moovzmatch",
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
            )
            self.client.admin.command("ping")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {e}")
            raise

        self.database = self.client[database_name]
        self.collection: Collection = self.database[collection_name]
        logger.info(
            f"Connected to MongoDB instance:\n Database: {database_name}\n Collection: {collection_name}"
        )

    def __enter__(self) -> "MongoClientWrapper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def initialize_indexes(self) -> None:
        """Initialize all indexes and the hybrid search retriever."""
        try:
            if self.collection_name == settings.MOVIES_COLLECTION:
                embedding_dim       = settings.MOVIE_NUM_DIMENSIONS
                index_name          = settings.MOVIE_INDEX_NAME
                text_path           = settings.MOVIE_TEXT_PATH
                embedding_path      = settings.MOVIE_EMBEDDING_PATH
                similarity_metric   = settings.MOVIE_SIMILARITY
            else:
                embedding_dim       = settings.TV_NUM_DIMENSIONS
                index_name          = settings.TV_INDEX_NAME
                text_path           = settings.TV_TEXT_PATH
                embedding_path      = settings.TV_EMBEDDING_PATH
                similarity_metric   = settings.TV_SIMILARITY

            if not self.retriever:
                self.retriever = self._get_hybrid_search_retriever(
                    text_key        =text_path,
                    embedding_key   =embedding_path,
                    index_name      =index_name,
                    similarity_metric=similarity_metric,
                )

            MongoIndex(
                retriever=self.retriever,
                collection=self.collection,
                collection_type=self.collection_name
            ).create(
                embedding_dim=embedding_dim,
                is_hybrid=False # Mongo M0 free clusters have a limit of 3 search and vector indexes per cluster.
            )
        except Exception as e:
            logger.error(f"Error initializing indexes: {e}")
            raise

    def clear_collection(self) -> None:
        """Remove all documents from the collection."""
        try:
            result = self.collection.delete_many({})
            logger.debug(
                f"Cleared collection. Deleted {result.deleted_count} documents."
            )
        except errors.PyMongoError as e:
            logger.error(f"Error clearing the collection: {e}")
            raise

    def ingest_document(self, document: T) -> str:
        """Insert a single document into the MongoDB collection."""
        try:
            doc_dict = self._serialize_document(document)
            result = self.collection.insert_one(doc_dict)
            document_id = str(result.inserted_id)
            logger.debug(f"Inserted document with ID: {document_id}")
            return document_id
        except errors.PyMongoError as e:
            logger.error(f"Error inserting document: {e}")
            raise

    def update_document(self, document_id: str, document: T) -> bool:
        """Update a document in the MongoDB collection."""
        try:
            doc_dict = self._serialize_document(document)
            result = self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": doc_dict}
            )
            if result.modified_count > 0:
                logger.debug(f"Updated document with ID: {document_id}")
                return True
            else:
                logger.warning(f"No document found with ID: {document_id}")
                return False
        except errors.PyMongoError as e:
            logger.error(f"Error updating document: {e}")
            raise

    def get_collection_count(self) -> int:
        """Return total number of documents in the collection."""
        try:
            return self.collection.count_documents({})
        except errors.PyMongoError as e:
            logger.error(f"Error counting documents in MongoDB: {e}")
            raise

    def _serialize_document(self, document: T) -> dict:
        """Serialize a Pydantic document for insertion/update."""
        if not isinstance(document, BaseModel):
            raise ValueError("Document must be a Pydantic model instance.")

        # Use specialized builder if applicable
        if self.collection_name == settings.MOVIES_COLLECTION and isinstance(document, MovieDetails):
            return movie_document.build(document)
        elif self.collection_name == settings.TV_COLLECTION and isinstance(document, TVDetails):
            return tv_document.build(document)
        return document.model_dump()

    def _get_hybrid_search_retriever(
        self,
        text_key:           str,
        embedding_key:      str,
        index_name:         str,
        similarity_metric:  str,
        k: int = settings.RAG_TOP_K
    ) -> MongoDBAtlasHybridSearchRetriever:
        """Get a hybrid search retriever for this collection."""
        if self.embedding_client is None or not self.embedding_client.embeddings:
            raise RuntimeError(
                "Embedding client is not initialized. "
                "Pass an embedding_client instance to MongoClientWrapper."
            )
        vectorstore = MongoDBAtlasVectorSearch.from_connection_string(
            connection_string=self.mongodb_uri,
            embedding=self.embedding_client.embeddings,
            namespace=f"{self.database_name}.{self.collection_name}",
            text_key=text_key,
            embedding_key=embedding_key,
            relevance_score_fn=similarity_metric,
        )
        return MongoDBAtlasHybridSearchRetriever(
            vectorstore=vectorstore,
            search_index_name=index_name,
            top_k=k,
            vector_penalty=settings.VECTOR_PENALTY,
            fulltext_penalty=settings.FULLTEXT_PENALTY
        )

    def close(self) -> None:
        """Close the MongoDB connection."""
        if not self._is_closed:
            try:
                self.client.close()
                self._is_closed = True
                logger.debug("Closed MongoDB connection.")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")

    def is_connected(self) -> bool:
        """Check if the MongoDB connection is still active."""
        if self._is_closed:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except errors.PyMongoError:
            return False
