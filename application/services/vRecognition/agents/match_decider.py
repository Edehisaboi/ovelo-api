from __future__ import annotations

import json
from typing import List, Dict, Any, cast

from application.core.config import settings
from application.services.vRecognition.state import State
from application.services.vRecognition.chains import get_ai_decider_chain, DeciderLLMOutput
from application.utils.agents import exception, extract_media_from_metadata


@exception
async def decide_match(state: State)-> Dict[str, Any]:
    candidates = cast(List[Dict[str, Any]], state.get("candidates") or [])
    if not candidates:
        return {}

    # Clear match, No need for AI decision
    candidates.sort(key=lambda c: float(c.get("metadata", {}).get("score", 0.0)), reverse=True)
    top_cand = candidates[0]
    top_score = float(top_cand.get("metadata", {}).get("score", 0.0))
    if top_score >= settings.ACCEPTANCE_THRESHOLD:
        media_type, media_id = extract_media_from_metadata(top_cand.get("metadata", {}))
        if media_type and media_id:
            return {
                "match": {
                    "type": media_type,
                    "id":   str(media_id)
                }
            }

    # Use AI decider chain for further decision-making
    chain = get_ai_decider_chain()
    actors_list: List[str] = state.get("actors") or []

    output: DeciderLLMOutput = await chain.ainvoke({
        "transcript":   state.get("transcript"),
        "actors":       ", ".join(actors_list),
        "candidates":   json.dumps(candidates)
    })

    if output.end:
        return {"end": True}
    
    if output.requery or not output.match:
        return {}

    return {
        "match": {
            "type": output.match.type,
            "id": output.match.id
        }
    }