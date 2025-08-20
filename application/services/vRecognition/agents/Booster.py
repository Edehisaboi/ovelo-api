from __future__ import annotations

from typing import List, Dict, Any, cast

from application.core.config import settings
from application.utils.agents import exception
from application.services.vRecognition.state import State


@exception
async def update_score(state: State) -> Dict[str, Any]:
    """Apply an actor-match bonus to candidate scores."""
    candidates = cast(List[Dict[str, Any]], state.get("candidates") or [])

    for cand in candidates:
        matched_count = len(
            cand["metadata"].get("matched_cast", [])
        )
        cand["metadata"]["score"] += (matched_count * settings.ACTOR_MATCH_BONUS)

    return {"candidates": candidates, "documents": None}
