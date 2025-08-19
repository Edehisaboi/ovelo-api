from __future__ import annotations

import orjson
from typing import List, Tuple, Optional, Dict, Any, cast
from typing_extensions import TypedDict
from collections import deque

from langchain_core.documents import Document

from application.core.config import settings
from application.services.vRecognition.state import State
from application.services.vRecognition.chains import get_ai_decider_chain, DeciderLLMOutput
from application.utils.agents import exception, extract_media_from_metadata, cid, split_cid


class StatValues(TypedDict):
    streak: int
    seq: int
    last_idx: Optional[int]


class Decider:
    MIN_GAP_RATIO = 0.10    # top1 must beat top2 by 10%
    MIN_STREAK    = 2       # same cid must be top1 in 2 consecutive turns
    MIN_INDEX     = 2       # require >=2 aligned index hits (forward within margin)
    INDEX_MARGIN  = 3       # ± margin around +1 forward progression

    def __init__(self) -> None:
        self.prev_top: Optional[str] = None
        # Per-cid stats to avoid cross-talk
        self.stats: Dict[str, StatValues] = {}
        self.rolling = deque(maxlen=settings.DECISION_WINDOW)

    @staticmethod
    def _cid_of(doc: Document) -> Optional[str]:
        mtype, mid = extract_media_from_metadata(doc.metadata)
        return cid(mtype, mid) if mtype and mid else None

    @staticmethod
    def _safe_index(doc: Document) -> Optional[int]:
        idx = doc.metadata.get("index")
        return int(idx) if idx is not None else None

    def _update_stats(self, top_cid: Optional[str], idx: Optional[int]) -> None:
        if not top_cid:
            return

        s = self.stats.get(top_cid)
        if s is None:
            s = cast(StatValues, {"streak": 0, "seq": 0, "last_idx": None})
            self.stats[top_cid] = s

        # Consecutive top-1 streak (reset if top changes)
        if top_cid == self.prev_top:
            s["streak"] += 1
        else:
            s["streak"] = 1
        self.prev_top = top_cid

        # Index continuity within same cid
        if idx is not None:
            last_idx = s["last_idx"]
            if isinstance(last_idx, int):
                delta = idx - last_idx
                # forward and within margin from +1
                if (delta >= 0) and (abs(delta - 1) <= self.INDEX_MARGIN):
                    s["seq"] += 1
                else:
                    # reset continuity window starting at current index
                    s["seq"] = 1
            else:
                # first valid index observation for this cid
                s["seq"] = 1
            s["last_idx"] = idx

    @exception
    async def decide(self, state: State) -> Dict[str, Any]:
        candidates = cast(List[Tuple[Document, float]], state.get("candidates") or [])
        if not candidates:
            self.rolling.append(0.0)
            return {}

        candidates.sort(key=lambda x: x[1], reverse=True)
        doc1, score1 = candidates[0]
        _, score2 = candidates[1] if len(candidates) > 1 else (None, 0.0)

        top_cid = self._cid_of(doc1)
        top_idx = self._safe_index(doc1)

        # Track rolling score for graceful “give up”
        self.rolling.append(float(score1))

        # 1) Threshold gate
        thr = settings.ACCEPTANCE_THRESHOLD
        if score1 < thr:
            if len(self.rolling) == self.rolling.maxlen and (sum(self.rolling) / len(self.rolling)) < thr:
                return {"end": True}
            return {}

        # 2) Gap gate
        gap_ok = True
        if len(candidates) > 1:
            gap_ok = (score1 - score2) >= (self.MIN_GAP_RATIO * score1)
        if not gap_ok:
            return {}

        # 3) Update continuity for current top
        self._update_stats(top_cid, top_idx)

        # 4) Persistence gates: consecutive top-1 + index continuity
        if top_cid:
            s = self.stats.get(top_cid, cast(StatValues, {"streak": 0, "seq": 0, "last_idx": None}))
            streak = s["streak"]
            seq = s["seq"]
            if streak >= self.MIN_STREAK and seq >= self.MIN_INDEX:
                media_type, media_id = split_cid(top_cid)
                return {
                    "match": {
                        "type": media_type,
                        "id":   media_id
                    }
                }

        return {}


@exception
async def ai_decider_node(state: State)-> Dict[str, Any]:
    transcript: str = state.get("transcript") or ""
    actors: list[str] = state.get("actors") or []
    candidates: list[Document] = cast(List[Document], state.get("candidates") or [])

    if not transcript or not actors or not candidates:
        return {"end": True}

    # Prepare candidates JSON for LLM
    candidates_json_str = orjson.dumps(
        [{"page_content": d.page_content, "metadata": d.metadata} for d in candidates],
        default=str,
        option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS | orjson.OPT_APPEND_NEWLINE
    ).decode("utf-8")

    chain = get_ai_decider_chain(transcript, ", ".join(actors), candidates_json_str)
    output: DeciderLLMOutput = await chain.ainvoke({})

    if output.end:
        return {"end": True}
    
    if output.requery:
        return {}

    if not output.match:
        return {}

    return {"match": {"type": output.match.type, "id": output.match.id}}