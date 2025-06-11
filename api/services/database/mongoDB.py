from typing import Generic, Type, TypeVar, Optional, List, Dict, Any
import time
from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel
from pymongo import MongoClient, errors
from pymongo.collection import Collection

from config import settings, get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class MongoClientWrapper(Generic[T]):
    """Service class for MongoDB operations, supporting ingestion, querying, and validation.

    This class provides methods to interact with MongoDB collections, including document
    ingestion, querying, and validation operations.

    Args:
        model (Type[T]): The Pydantic model class to use for document serialization.
        collection_name (str): Name of the MongoDB collection to use.
        database_name (str, optional): Name of the MongoDB database to use.
        mongodb_uri (str, optional): URI for connecting to MongoDB instance.

    Attributes:
        model (Type[T]): The Pydantic model class used for document serialization.
        collection_name (str): Name of the MongoDB collection.
        database_name (str): Name of the MongoDB database.
        mongodb_uri (str): MongoDB connection URI.
        client (MongoClient): MongoDB client instance for database connections.
        database (Database): Reference to the target MongoDB database.
        collection (Collection): Reference to the target MongoDB collection.
    """

    def __init__(
            self,
            model: Type[T],
            collection_name: str,
            database_name: str = settings.MONGODB_DB,
            mongodb_uri: str = settings.MONGODB_URL
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

        self.model = model
        self.collection_name = collection_name
        self.database_name = database_name
        self.mongodb_uri = mongodb_uri

        try:
            self.client = MongoClient(mongodb_uri, appname="moovzmatch")
            self.client.admin.command("ping")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDBService: {e}")
            raise

        self.database = self.client[database_name]
        self.collection = self.database[collection_name]
        logger.info(
            f"Connected to MongoDB instance:\n Database: {database_name}\n Collection: {collection_name}"
        )

    def __enter__(self) -> "MongoClientWrapper":
        """Enable context manager support.

        Returns:
            MongoDBService: The current instance.
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

            doc_dict = document.model_dump()
            doc_dict["created_at"] = datetime.utcnow()
            doc_dict["updated_at"] = datetime.utcnow()

            result = self.collection.insert_one(doc_dict)
            document_id = str(result.inserted_id)

            logger.debug(f"Inserted document with ID: {document_id}")
            return document_id

        except errors.PyMongoError as e:
            logger.error(f"Error inserting document: {e}")
            raise

    def update_document(self, document_id: str, document: T) -> bool:
        try:
            if not isinstance(document, BaseModel):
                raise ValueError("Document must be a Pydantic model instance.")

            doc_dict = document.model_dump()
            doc_dict["updated_at"] = datetime.utcnow()

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

    def fetch_document(self, document_id: str) -> Optional[T]:
        try:
            result = self.collection.find_one({"_id": ObjectId(document_id)})
            if result:
                return self.model(**result)
            return None
        except errors.PyMongoError as e:
            logger.error(f"Error fetching document: {e}")
            raise

    def get_collection_count(self) -> int:
        """Count the total number of documents in the collection.

        Returns:
            Total number of documents in the collection.

        Raises:
            errors.PyMongoError: If the count operation fails.
        """

        try:
            return self.collection.count_documents({})
        except errors.PyMongoError as e:
            logger.error(f"Error counting documents in MongoDB: {e}")
            raise

    def close(self) -> None:
        """Close the MongoDB connection.

        This method should be called when the service is no longer needed
        to properly release resources, unless using the context manager.
        """

        self.client.close()
        logger.debug("Closed MongoDB connection.")

    def create_vector_index(
        self,
        field_path: str,
        dimensions: int,
        similarity_metric: str = "cosine"
    ) -> None:
        """Create a vector search index for the specified field."""
        try:
            index_definition = {
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        field_path: {
                            "type": "knnVector",
                            "dimensions": dimensions,
                            "similarity": similarity_metric
                        }
                    }
                }
            }

            self.database.command({
                "createSearchIndex": self.collection_name,
                "definition": index_definition
            })
            logger.info(f"Created vector index for field: {field_path}")

        except errors.PyMongoError as e:
            logger.error(f"Error creating vector index: {e}")
            raise

    def create_text_index(self, fields: List[str]) -> None:
        """Create a text search index for the specified fields."""
        try:
            index_definition = {
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        field: {"type": "string", "analyzer": "lucene.standard"}
                        for field in fields
                    }
                }
            }

            self.database.command({
                "createSearchIndex": self.collection_name,
                "definition": index_definition
            })
            logger.info(f"Created text index for fields: {fields}")

        except errors.PyMongoError as e:
            logger.error(f"Error creating text index: {e}")
            raise

    def vector_search(
        self,
        query_vector: List[float],
        field_path: str,
        limit: int = 10,
        filter_query: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform a vector similarity search."""
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": f"{self.collection_name}_vector",
                        "path": field_path,
                        "queryVector": query_vector,
                        "numCandidates": limit * 2,
                        "limit": limit,
                        "filter": filter_query or {}
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "score": {"$meta": "vectorSearchScore"},
                        "document": "$$ROOT"
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            return [doc["document"] for doc in results]

        except errors.PyMongoError as e:
            logger.error(f"Error performing vector search: {e}")
            raise

    def hybrid_search(
        self,
        query_vector: List[float],
        text_query: str,
        vector_field: str,
        text_fields: List[str],
        limit: int = 10,
        filter_query: Optional[Dict[str, Any]] = None,
        vector_weight: float = 0.7,
        text_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Perform a hybrid search combining vector and text search."""
        try:
            pipeline = [
                {
                    "$search": {
                        "index": f"{self.collection_name}_hybrid",
                        "compound": {
                            "should": [
                                {
                                    "vectorSearch": {
                                        "path": vector_field,
                                        "queryVector": query_vector,
                                        "numCandidates": limit * 2,
                                        "score": {"boost": {"value": vector_weight}}
                                    }
                                },
                                {
                                    "text": {
                                        "query": text_query,
                                        "path": text_fields,
                                        "score": {"boost": {"value": text_weight}}
                                    }
                                }
                            ],
                            "filter": filter_query or {}
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "score": {"$meta": "searchScore"},
                        "document": "$$ROOT"
                    }
                },
                {"$limit": limit}
            ]

            results = list(self.collection.aggregate(pipeline))
            return [doc["document"] for doc in results]

        except errors.PyMongoError as e:
            logger.error(f"Error performing hybrid search: {e}")
            raise
