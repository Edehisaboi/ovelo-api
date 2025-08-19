from __future__ import annotations

from typing import List, Tuple, Dict, Any, cast

from langchain_core.documents import Document

from application.core.config import settings
from application.utils.agents import exception, extract_media_from_metadata
from application.services.vRecognition.state import State


@exception
async def update_score(state: State) -> Dict[str, Any]:
    """Apply an actor-match bonus to candidate scores."""
    candidates = cast(List[Tuple[Document, float]], state.get("candidates") or [])
    actors: List[str] = state.get("actors") or []

    actor_matches: Dict[str, Dict[str, Any]] = state.get("actor_matches") or {}
    updated_candidates: List[Tuple[Document, float]] = []

    total_actors = max(len(actors), 1)

    for doc, score in candidates:
        media_type, media_id = extract_media_from_metadata(doc.metadata)
        if not media_type or not media_id:
            continue

        presence_info = actor_matches.get(media_id) or {}
        #exists: bool = bool(presence_info.get("exists", False))
        missing: List[str] = presence_info.get("missing", [])
        matched_count = max(total_actors - len(missing), 0)

        bonus = settings.ACTOR_MATCH_BONUS * matched_count
        updated_candidates.append((doc, score + bonus))

    return {
        "candidates": sorted(updated_candidates, key=lambda item: item[1], reverse=True),
        "documents": None,
    }
