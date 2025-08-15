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

    for doc, score in candidates:
        media_type, media_id = extract_media_from_metadata(doc.metadata)
        if not media_type or not media_id:
            continue
        data = actor_matches.get(media_id)
        if not data:
            updated.append((doc, score))
            continue
        exists = data.get("exists", False)
        missing = data.get("missing", [])

        bonus = settings.ACTOR_MATCH_BONUS * len(actors) if exists else (
            settings.ACTOR_MATCH_BONUS * max(len(actors) - len(missing), 0)
        )
        updated.append((doc, score + bonus))

    return {
        "candidates": updated,
        "documents": None
    }
 

