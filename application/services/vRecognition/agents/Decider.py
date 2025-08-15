import time
from typing import List, Tuple
from collections import deque

from langchain_core.documents import Document

from application.services.vRecognition.queue import TopKQueue
from application.core.config import settings
from application.services.vRecognition.state import State
from application.services.vRecognition.utils import exception, extract_media_from_metadata, cid


class Decider:
    def __init__(self):
        self.top_k_queue = TopKQueue(k=settings.RAG_TOP_K)
        self.rolling_top_scores = deque(maxlen=settings.DECISION_ROLLING_WINDOW)

    @exception
    async def decide(self, state: State):
        if not state["candidates"]:
            self.rolling_top_scores.append(0.0)
            return {}

        candidates: List[Tuple[Document, float]] = state["candidates"]
        for doc, score in candidates:
            media_type, media_id = extract_media_from_metadata(doc.metadata)
            if not media_type or not media_id:
                continue
            cid_key = cid(media_type, media_id)
            self.top_k_queue.push(cid_key, score)

        top_candidate_cid, top_score = self.top_k_queue.top() or (None, 0.0)
        if top_candidate_cid:
            self.rolling_top_scores.append(top_score)

        # Now decide
        if top_score >= settings.ACCEPTANCE_THRESHOLD:
            return {
                "match": top_candidate_cid
            }

        if len(self.rolling_top_scores) == self.rolling_top_scores.maxlen:
            average_score = sum(self.rolling_top_scores) / len(self.rolling_top_scores)
            if average_score < settings.ACCEPTANCE_THRESHOLD:
                return {
                    "end": True
                }

        return {}
