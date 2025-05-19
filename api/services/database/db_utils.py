import logging
from pymongo.collection import Collection
from typing import Dict, List, Union, Optional
from bson import ObjectId
from functools import lru_cache
from config import Settings

# Configure logging
logging.basicConfig(
    level=Settings.LOG_LEVEL,
    format=Settings.LOG_FORMAT,
    filename=Settings.LOG_FILE
)
logger = logging.getLogger(__name__)

# Cache decorator with settings
def cache_result(ttl: Optional[int] = None, max_size: Optional[int] = None):
    """
    Cache decorator that uses settings for TTL and max size.
    """
    def decorator(func):
        return lru_cache(maxsize=max_size or Settings.CACHE_MAX_SIZE)(func)
    return decorator

@cache_result(ttl=Settings.CACHE_TTL)
def insert_document(collection: Collection, document: Dict) -> str:
    """
    Inserts a single document into the collection.
    Returns the string version of the inserted ObjectId.
    """
    try:
        result = collection.insert_one(document)
        logger.info(f"Inserted document with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Failed to insert document: {str(e)}")
        raise

@cache_result(ttl=Settings.CACHE_TTL)
def insert_documents(collection: Collection, documents: List[Dict]) -> List[str]:
    """
    Inserts multiple documents into the collection.
    Returns a list of string ObjectIds.
    """
    try:
        result = collection.insert_many(documents)
        logger.info(f"Inserted {len(documents)} documents")
        return [str(doc_id) for doc_id in result.inserted_ids]
    except Exception as e:
        logger.error(f"Failed to insert documents: {str(e)}")
        raise

@cache_result(ttl=Settings.CACHE_TTL)
def delete_by_id(collection: Collection, document_id: Union[str, ObjectId]) -> int:
    """
    Deletes a single document by its _id.
    Returns the number of documents deleted (0 or 1).
    """
    try:
        if isinstance(document_id, str):
            document_id = ObjectId(document_id)
        result = collection.delete_one({"_id": document_id})
        logger.info(f"Deleted document with ID: {document_id}")
        return result.deleted_count
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise

@cache_result(ttl=Settings.CACHE_TTL)
def delete_many_by_filter(collection: Collection, filter_query: Dict) -> int:
    """
    Deletes all documents that match the filter query.
    Returns the number of documents deleted.
    """
    try:
        result = collection.delete_many(filter_query)
        logger.info(f"Deleted {result.deleted_count} documents matching filter")
        return result.deleted_count
    except Exception as e:
        logger.error(f"Failed to delete documents: {str(e)}")
        raise

def clear_cache():
    """
    Clears all cached results.
    """
    for func in [insert_document, insert_documents, delete_by_id, delete_many_by_filter]:
        func.cache_clear()
    logger.info("Cleared all database operation caches")
