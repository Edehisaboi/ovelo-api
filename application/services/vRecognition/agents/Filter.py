from __future__ import annotations

from typing import List, Dict, Tuple, Any

from langchain_core.documents import Document

from application.core.config import settings
from application.utils.agents import exception, extract_media_from_metadata, cid
from application.services.vRecognition.state import State


def _select_best_documents(documents: List[Document]) -> Dict[str, Tuple[Document, float]]:
    """Deduplicate by media id and keep the highest-scoring document per id."""
    best_by_media_id: Dict[str, Tuple[Document, float]] = {}

    for doc in documents:
        metadata = doc.metadata or {}
        score = metadata.get("score")
        if not isinstance(score, (int, float)) or score < settings.MIN_SCORE_GATE:
            continue

        media_type, media_id = extract_media_from_metadata(metadata)
        if not media_type or not media_id:
            continue

        composite_id = cid(media_type, media_id)
        previous = best_by_media_id.get(composite_id)
        if previous is None or float(score) > previous[1]:
            best_by_media_id[composite_id] = (doc, float(score))

    return best_by_media_id


@exception
async def process_document(state: State) -> Dict[str, Any]:
    """Select top-K scored candidates as (Document, score) tuples for downstream scoring/decisions."""
    documents: List[Document] = state.get("documents") or []
    best_by_media_id = _select_best_documents(documents)

    candidates: List[Tuple[Document, float]] = sorted(
        best_by_media_id.values(), key=lambda item: item[1], reverse=True
    )[: settings.RAG_TOP_K]
    return {"candidates": candidates, "documents": None}


@exception
async def filter_document(state: State) -> Dict[str, Any]:
    """Select top-K documents only (without scores) for LLM-based decisions."""
    documents: List[Document] = state.get("documents") or []
    best_by_media_id = _select_best_documents(documents)

    candidates: List[Document] = [
        doc for doc, _ in sorted(best_by_media_id.values(), key=lambda item: item[1], reverse=True)
    ][: settings.RAG_TOP_K]
    return {"candidates": candidates, "documents": None}
