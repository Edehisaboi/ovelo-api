from typing import (
    Generic, Type, TypeVar, Optional, Dict, Any, List, Union
)

from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection

T = TypeVar("T", bound=BaseModel)


class CollectionWrapper(Generic[T]):
    """Wrapper for a single MongoDB collection with type safety."""

    def __init__(
        self,
        model:           Type[T] | type(dict),
        collection:      AsyncIOMotorCollection,
        collection_name: str
    ):
        self.model           = model
        self.collection      = collection
        self.collection_name = collection_name

    async def insert_one(
        self,
        document: Union[T, dict]
    ) -> str:
        """Insert a single document and return its ID. Raises if insertion fails."""
        doc_dict = self._serialize_document(document)
        result = await self.collection.insert_one(doc_dict)
        if not result.inserted_id:
            raise RuntimeError(f"Failed to insert document: {doc_dict}")
        return str(result.inserted_id)

    async def insert_many(
        self,
        documents: List[Union[T, dict]]
    ) -> List[str]:
        """Insert multiple documents and return their IDs. Raises if insertion fails or IDs missing."""
        doc_dicts = [self._serialize_document(doc) for doc in documents]
        result = await self.collection.insert_many(doc_dicts)
        if not result.inserted_ids or len(result.inserted_ids) != len(doc_dicts):
            raise RuntimeError(
                f"Failed to insert all documents: expected {len(doc_dicts)}, got {len(result.inserted_ids) if result.inserted_ids else 0}"
            )
        return [str(id) for id in result.inserted_ids]

    async def find_one(
        self,
        filter_dict: Dict[str, Any]
    ) -> Optional[T]:
        doc = await self.collection.find_one(filter_dict)
        if doc:
            if self.model == dict:
                return doc
            return self.model.model_validate(doc)
        return None

    async def find_many(
        self,
        filter_dict: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[T]:
        cursor = self.collection.find(filter_dict)
        if limit:
            cursor = cursor.limit(limit)
        docs = await cursor.to_list(length=limit or 100)
        if self.model == dict:
            return [doc for doc in docs]
        return [self.model.model_validate(doc) for doc in docs]

    async def update_one(
        self,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any]
    ) -> bool:
        result = await self.collection.update_one(filter_dict, {"$set": update_dict})
        return result.modified_count > 0

    async def delete_one(
        self,
        filter_dict: Dict[str, Any]
    ) -> bool:
        result = await self.collection.delete_one(filter_dict)
        return result.deleted_count > 0

    async def count(
        self,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> int:
        return await self.collection.count_documents(filter_dict or {})

    @staticmethod
    def _serialize_document(document: Union[T, dict]) -> dict:
        if isinstance(document, BaseModel):
            return document.model_dump()
        elif isinstance(document, dict):
            return document
        else:
            raise ValueError("Document must be a Pydantic model instance or dict.")
