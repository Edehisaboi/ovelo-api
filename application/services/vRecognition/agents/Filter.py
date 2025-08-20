from __future__ import annotations

from typing import List, Dict, Tuple, Any

from langchain_core.documents import Document

from application.core.config import settings
from application.utils.agents import exception, extract_media_from_metadata, cid
from application.services.vRecognition.state import State


DROP_META_KEYS = {
    "_id",
    "vector_score",
    "fulltext_score",
    "rank",
    "episode_id",
    "season_number",
    "episode_number",
}


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
        prev = best_by_media_id.get(composite_id)
        if prev is None or float(score) > prev[1]:
            best_by_media_id[composite_id] = (doc, float(score))

    return best_by_media_id


def _sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    if not meta:
        return {}
    clean = {k: v for k, v in meta.items() if k not in DROP_META_KEYS}
    return clean


def _doc_to_json(doc: Document) -> Dict[str, Any]:
    meta = _sanitize_metadata(doc.metadata or {})
    return {
        "metadata": meta,
        "page_content": doc.page_content,
    }


@exception
async def filter_document(state: State) -> Dict[str, Any]:
    documents: List[Document] = state.get("documents") or []
    best_by_media_id = _select_best_documents(documents)

    # Order by score desc, take top-K
    top_docs: List[Tuple[Document, float]] = sorted(
        best_by_media_id.values(), key=lambda item: item[1], reverse=True
    )[: settings.RAG_TOP_K]

    # Convert to JSON dicts and strip unwanted fields
    candidates: List[Dict[str, Any]] = [_doc_to_json(doc) for doc, _score in top_docs]
    if not candidates:
        return {
            "end": True
        }

    return {"candidates": candidates, "documents": None}
