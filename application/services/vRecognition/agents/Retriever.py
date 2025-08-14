from typing import List

from langchain_core.documents import Document

from infrastructure.database.mongodb import MongoCollectionsManager
from application.services.vRecognition.utils import exception
from application.services.vRecognition.state import State


class Retriever:
    def __init__(self, mongo_db: MongoCollectionsManager):
        self.mongo_db = mongo_db

    @exception
    async def execute(self, state: State):
        if not self.mongo_db:
            raise ValueError("MongoDB collections manager is not initialized.")

        text = state.get("transcript") or ""
        if not text:
            return {}
        documents: List[Document] = await self.mongo_db.perform_hybrid_search(text)

        return {
            "documents": documents
        }
 

