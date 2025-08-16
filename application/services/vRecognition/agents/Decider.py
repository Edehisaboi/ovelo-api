from typing import List, Tuple
from collections import deque

from langchain_core.documents import Document

from application.core.config import settings
from application.services.vRecognition.state import State
from application.services.vRecognition.utils import exception, extract_media_from_metadata, cid


class Decider:
    MIN_GAP_RATIO = 0.10    # top1 must beat top2 by 10%
    MIN_STREAK = 2          # appear as top1 in 2 consecutive frames

    def __init__(self):
        self.prev_top: str | None = None
        self.streak: int = 0
        self.rolling = deque(maxlen=settings.DECISION_ROLLING_WINDOW)

    @staticmethod
    def _cid_of(doc: Document) -> str | None:
        mtype, mid = extract_media_from_metadata(doc.metadata)
        return cid(mtype, mid) if mtype and mid else None

    @exception
    async def decide(self, state: State):
        candidates: List[Tuple[Document, float]] = state["candidates"] or []
        if not candidates:
            self.rolling.append(0.0)
            return {}

        # Sort candidates by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        (doc1, score1) = candidates[0]
        top_cid = self._cid_of(doc1)
        (doc2, score2) = (candidates[1] if len(candidates) > 1 else (None, 0.0))

        # update streak
        if top_cid and top_cid == self.prev_top:
            self.streak += 1
        else:
            self.prev_top = top_cid
            self.streak = 1

        self.rolling.append(score1)

        # Threshold check
        if score1 < settings.ACCEPTANCE_THRESHOLD:
            if len(self.rolling) == self.rolling.maxlen and (sum(self.rolling) / len(self.rolling)) < settings.ACCEPTANCE_THRESHOLD:
                return {"end": True}
            return {}

        # Gap check
        gap_ok = True
        if len(candidates) > 1:
            gap_ok = (score1 - score2) >= (self.MIN_GAP_RATIO * score1)

        # Persistence check
        if top_cid and gap_ok and self.streak >= self.MIN_STREAK:
            return {
                "match": top_cid
            }

        return {}
