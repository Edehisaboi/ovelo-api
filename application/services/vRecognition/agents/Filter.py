from typing import List

from langchain_core.documents import Document

from application.core.config import settings
from application.services.vRecognition.utils import exception
from application.services.vRecognition.state import State


@exception
def process_document(state: State):
    documents: List[Document] = state.get("documents") or []
    candidates: List[tuple[Document, float]] = []
    for doc in documents:
        metadata = doc.metadata
        score = metadata.get("score")
        if isinstance(score, (int, float)) and score >= settings.MIN_SCORE_GATE:
            candidates.append((doc, float(score)))

    return {
        "candidates": candidates,
        "documents": None
    }
 

