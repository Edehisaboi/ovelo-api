from typing import List, Tuple, Dict, Any

from langchain_core.documents import Document

from application.core.config import settings
from application.services.vRecognition.utils import exception, extract_media_from_metadata
from application.services.vRecognition.state import State


@exception
async def update_score(state: State):
    candidates: List[Tuple[Document, float]] = state.get("candidates") or []
    actors:     List[str] = state.get("actors") or []

    actor_matches:  Dict[str, Dict[str, Any]] = state.get("actor_matches") or {}
    updated:        List[Tuple[Document, float]] = []

    total = max(len(actors), 1)

    for doc, score in candidates:
        media_type, media_id = extract_media_from_metadata(doc.metadata)
        if not media_type or not media_id:
            continue

        data = actor_matches.get(media_id) or {}
        exists = data.get("exists", False)
        missing = data.get("missing", [])
        matched = max(total - len(missing), 0) if total else 0
        match_ratio = matched / total  # 0..1

        # Stronger signal if "exists" came back True, but still value for partial matches
        actor_conf = max(match_ratio, 1.0 if exists else 0.0) if exists else match_ratio

        bonus = settings.ACTOR_MATCH_BONUS * actor_conf
        updated.append((doc, score + bonus))

    return {"candidates": sorted(updated, key=lambda x: x[1], reverse=True), "documents": None}
