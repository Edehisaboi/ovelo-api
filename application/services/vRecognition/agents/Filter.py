from typing import List, Dict , Tuple

from langchain_core.documents import Document

from application.core.config import settings
from application.services.vRecognition.utils import exception, extract_media_from_metadata, cid
from application.services.vRecognition.state import State


@exception
async def process_document(state: State):
    documents: List[Document] = state.get("documents") or []
    best: Dict[str, Tuple[Document, float]] = {}

    for doc in documents:
        meta = doc.metadata or {}
        score = meta.get("score")
        if not isinstance(score, (int, float)) or score < settings.MIN_SCORE_GATE:
            continue
        media_type, media_id = extract_media_from_metadata(meta)
        if not media_type or not media_id:
            continue
        key = cid(media_type, media_id)
        prev = best.get(key)
        if prev is None or float(score) > prev[1]:
            best[key] = (doc, float(score))

    # Sort and cap K to reduce downstream cost
    candidates = sorted(best.values(), key=lambda x: x[1], reverse=True)[:settings.RAG_TOP_K]
    return {"candidates": candidates, "documents": None}
