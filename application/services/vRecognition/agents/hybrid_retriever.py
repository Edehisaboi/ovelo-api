from __future__ import annotations

from typing import List, Dict, Any

from langchain_core.documents import Document

from infrastructure.database.mongodb import MongoCollectionsManager
from application.utils.agents import exception
from application.services.vRecognition.state import State


class Retriever:
    """Queries hybrid search over movie and TV chunk stores using the transcript text."""

    def __init__(self, mongo_db: MongoCollectionsManager) -> None:
        self.mongo_db: MongoCollectionsManager = mongo_db

    @exception
    async def retrieve_documents(self, state: State) -> Dict[str, Any]:
        if not self.mongo_db:
            raise ValueError("MongoDB collections manager is not initialized.")

        transcript_text = state.get("transcript") or ""
        if not transcript_text:
            return {}

        documents: List[Document] = await self.mongo_db.perform_hybrid_search(transcript_text)
        return {"documents": documents}
 

