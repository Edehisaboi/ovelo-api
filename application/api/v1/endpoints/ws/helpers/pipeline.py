import time
from datetime import datetime, timezone
from collections import deque
from typing import Dict, Any, Optional, List, Callable, Awaitable

import asyncio
from contextlib import suppress
from pydantic import BaseModel, Field
from langchain_core.documents import Document

from application.core.config import settings
from infrastructure.database.mongodb import MongoCollectionsManager
from infrastructure.database.queries import has_actors
from application.core.logging import get_logger
from external.clients.transcribe import AWSTranscribeRealtimeSTTClient
from .queue import TopKQueue
from .utils import (
    extract_media_from_metadata,
    fetch_media_summary,
    notify_update,
    safe_float,
    split_cid,
    cid,
)

logger = get_logger(__name__)

class MediaResult(BaseModel):
    id:           Optional[str]   = None
    title:        Optional[str]   = None
    posterUrl:    Optional[str]   = None
    year:         Optional[str]   = None
    director:     Optional[str]   = None
    genre:        Optional[str]   = None
    description:  Optional[str]   = None
    trailerUrl:   Optional[str]   = None
    tmdbRating:   Optional[float] = None
    imdbRating:   Optional[float] = None
    duration:     Optional[int]   = None
    identifiedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source:       Optional[str]   = "camera"

class StreamResponse(BaseModel):
    success:        bool
    sessionId:      str
    result:         Optional[MediaResult]   = None
    confidence:     Optional[float]         = None
    processingTime: Optional[float]         = None
    alternatives:   Optional[list[MediaResult]] = None
    error:          Optional[str]           = None

class MediaResultPayload(BaseModel):
    type: str = "result"
    data: StreamResponse

# TODO: DO SAME FOR UPDATES, FRONTEND NEEDS TO BE UPDATED AS WELL TO FIT THIS


class IdentificationPipeline:
    """Per-session real-time pipeline storing actors and transcript, with a live STT stream."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.actors: list[str] = []
        self.final_utterances: list[str] = []
        self.current_partial: Optional[str] = None
        self.created_at = datetime.now(timezone.utc).isoformat()

        self._audio_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._stt_task: Optional[asyncio.Task] = None
        self._closing: bool = False

        # event-driven refine and single-flight guard
        self._evt_text: asyncio.Event = asyncio.Event()
        self._evt_actor: asyncio.Event = asyncio.Event()
        self._search_lock: asyncio.Lock  = asyncio.Lock()

        # result channel + background run task
        self._result_q: asyncio.Queue[MediaResultPayload] = asyncio.Queue()
        self._run_task: Optional[asyncio.Task] = None

        # notify throttling
        self._last_notify_id: Optional[str] = None
        self._last_notify_score: float = 0.0

    @property
    def transcript_text(self) -> str:
        parts = self.final_utterances[:]
        if self.current_partial:
            parts.append(self.current_partial)
        return " ".join(parts).strip()

    async def push_audio_chunk(self, audio_b64: str) -> None:
        await self._audio_queue.put(audio_b64)

    def update_actors(self, names: list[str]) -> None:
        if not names:
            return
        updated = False
        existing = set(self.actors)
        for name in names:
            if name not in existing:
                self.actors.append(name)
                existing.add(name)
                updated = True
        if updated:
            self._evt_actor.set()

    def start(self, *, run_coro) -> None:
        if self._run_task and not self._run_task.done():
            return
        self._run_task = asyncio.create_task(run_coro)

    def reset(self) -> None:
        """Reset pipeline state to allow a fresh identification run."""
        self.actors.clear()
        self.final_utterances.clear()
        self.current_partial = None
        self._evt_actor.clear()
        self._evt_text.clear()
        self._last_notify_id = None
        self._last_notify_score = 0.0
        self._closing = False
        self._audio_queue = asyncio.Queue()
        if self._run_task and self._run_task.done():
            self._run_task = None

    async def wait_final_result(self) -> MediaResultPayload:
        return await self._result_q.get()

    async def _audio_generator(self):
        while True:
            chunk = await self._audio_queue.get()
            if chunk is None:
                break
            yield chunk

    async def _on_transcript(self, event: Dict[str, Any]):
        text = (event.get("text") or "").strip()
        if not text:
            return

        is_partial = bool(event.get("is_partial", False))

        if is_partial:
            self.current_partial = text
        else:
            self.final_utterances.append(text)
            self.current_partial = None

            self._evt_text.set() # todo: only set on significant change

    def ensure_stt_stream(self, stt_client: AWSTranscribeRealtimeSTTClient) -> None:
        if self._stt_task and not self._stt_task.done():
            return

        async def _run():
            try:
                await stt_client.transcribe(
                    self._audio_generator(),
                    on_transcript=self._on_transcript,
                )
            except Exception as e:
                logger.error(f"STT stream failed for session {self.session_id}: {e}")

        self._stt_task = asyncio.create_task(_run())

    async def run(
        self,
        mongo_db: MongoCollectionsManager,
        top_k: int = 10,
        accept_threshold: float = 0.59,  # todo: can this be dynamic? higher with more actors? and lower for just text?
        min_score_gate: float = 0.40,  # normalized
        history_window: int = 5,
        max_wait_sec: float = 30.0,
        actor_weight: float = 0.08,
        *,
        on_update: Optional[Callable[[dict], Awaitable[None]]] = None,
        notify_improvement_epsilon: float = 0.02,
        stop_after_match: bool = True
    ) -> MediaResultPayload:
        top_k_queue = TopKQueue(k=top_k)
        rolling_top_scores = deque(maxlen=history_window)
        start_monotonic = time.monotonic()

        per_vector_max = 1.0 / (settings.VECTOR_PENALTY + 1.0)
        per_text_max = 1.0 / (settings.FULLTEXT_PENALTY + 1.0)
        hybrid_maximum = max(per_vector_max + per_text_max, 1e-9)

        def _normalize_rrf(score: float) -> float:
            normalized = safe_float(score / hybrid_maximum)
            return 0.0 if normalized < 0 else (1.0 if normalized > 1.0 else normalized)

        # inner utility: evaluate acceptance/rejection
        def _decide(now_monotonic: float) -> Optional[Dict[str, Any]]:
            top_candidate = top_k_queue.top()
            if top_candidate:
                _, top_score_local = top_candidate
                if top_score_local >= accept_threshold:
                    return {"accept": True, "top": top_candidate}

            waited_seconds = now_monotonic - start_monotonic
            if waited_seconds >= max_wait_sec and len(rolling_top_scores) == rolling_top_scores.maxlen:
                average_score = sum(rolling_top_scores) / len(rolling_top_scores)
                if average_score < accept_threshold:
                    return {"accept": False, "top": top_k_queue.top()}
            return None

        try:
            while not self._closing:
                time_remaining = max(0.0, max_wait_sec - (time.monotonic() - start_monotonic))
                if time_remaining <= 0.0:
                    result = MediaResultPayload(
                        data=StreamResponse(
                            success=False,
                            sessionId=self.session_id,
                            error="timeout"
                        )
                    )
                    await self._result_q.put(result)
                    return result

                wait_text   = asyncio.create_task(self._evt_text.wait())
                wait_actor  = asyncio.create_task(self._evt_actor.wait())
                done, pending = await asyncio.wait(
                    {wait_text, wait_actor},
                    timeout=time_remaining,
                    return_when=asyncio.FIRST_COMPLETED
                )
                # Clean-up pending waits
                for t in pending:
                    t.cancel()

                # Timeout -> rejection check
                if not done:
                    result = MediaResultPayload(
                        data=StreamResponse(
                            success=False,
                            sessionId=self.session_id,
                            error="timeout"
                        )
                    )
                    await self._result_q.put(result)
                    return result

                # Check if we got text or actor updates
                actors_updated = self._evt_actor.is_set()
                text_updated = self._evt_text.is_set()
                if actors_updated:
                    self._evt_actor.clear()
                if text_updated:
                    self._evt_text.clear()

                # Single-flight guard
                async with self._search_lock:
                    text = self.transcript_text
                    # todo: remove this check in future, when we have better text processing
                    if not text or len(text) < 60:
                        continue

                    logger.info(f"Processing text: {text}")

                    documents: List[Document] = await mongo_db.perform_hybrid_search(text)

                    # Base candidates
                    candidates: List[tuple[Document, float]] = []
                    for doc in (documents or []):
                        metadata = doc.metadata
                        raw_score = metadata.get("score")
                        base_score = _normalize_rrf(raw_score)
                        print(base_score)
                        if base_score >= min_score_gate:
                            candidates.append((doc, base_score))

                    if not candidates:
                        rolling_top_scores.append(0.0)
                        if self._last_notify_id is not None:
                            self._last_notify_id = None
                            self._last_notify_score = 0.0
                            await notify_update(
                                on_update,
                                {
                                    "type": "update",
                                    "session_id": self.session_id,
                                    "status": "no_candidates",
                                }
                            )
                        continue

                    candidates.sort(key=lambda x: x[1], reverse=True)
                    to_validate = candidates[:5]  # Top 5 candidates for actor validation

                    if self.actors and actors_updated:
                        movie_ids: List[str] = []
                        tv_ids: List[str] = []
                        for doc, _ in to_validate:
                            metadata = doc.metadata
                            media_type, media_id = extract_media_from_metadata(metadata)
                            if media_type == "movie" and media_id:
                                movie_ids.append(media_id)
                            elif media_type == "tv" and media_id:
                                tv_ids.append(media_id)

                        batch_results: Dict[str, Dict[str, Any]] = {}
                        if movie_ids:
                            movie_actor_presence = await has_actors(mongo_db, movie_ids, self.actors, "movie")
                            if movie_actor_presence:
                                batch_results.update(movie_actor_presence)
                        if tv_ids:
                            tv_actor_presence = await has_actors(mongo_db, tv_ids, self.actors, "tv")
                            if tv_actor_presence:
                                batch_results.update(tv_actor_presence)

                        for doc, base_score in to_validate:
                            metadata = doc.metadata
                            media_type, media_id = extract_media_from_metadata(metadata)
                            if not media_type or not media_id:
                                continue
                            cid_key = cid(media_type, media_id)
                            data = batch_results.get(media_id)
                            if not data:
                                top_k_queue.push(cid_key, base_score)
                                continue
                            exists = data.get("exists", False)
                            missing = data.get("missing", [])

                            num_actors = len(self.actors)  # TODO: Remove factor from bonus calculation in future
                            bonus = actor_weight if exists else (
                                actor_weight * (num_actors - len(missing)) / num_actors if num_actors else 0.0
                            )
                            top_k_queue.push(cid_key, min(base_score + bonus, 1.0))
                    else:
                        # No actors change: Push base candidates directly
                        for doc, base_score in candidates:
                            metadata = doc.metadata
                            media_type, media_id = extract_media_from_metadata(metadata)
                            if not media_type or not media_id:
                                continue
                            cid_key = cid(media_type, media_id)
                            top_k_queue.push(cid_key, base_score)

                    # Rolling history and incremental notification
                    top_entry = top_k_queue.top()
                    if top_entry:
                        top_candidate_cid, top_score = top_entry
                        rolling_top_scores.append(top_score)
                        improved = (
                            self._last_notify_id != top_candidate_cid or
                            abs(top_score - self._last_notify_score) >= notify_improvement_epsilon
                        )
                        if improved:
                            self._last_notify_id = top_candidate_cid
                            self._last_notify_score = top_score

                            media_type, media_id = split_cid(top_candidate_cid)
                            # Todo: use this data, come back to this
                            #_ = await fetch_media_summary(mongo_db, media_type, media_id)
                            await notify_update(on_update, {
                                "type": "update",
                                "session_id": self.session_id
                            })

                    # Final decision?
                    decision = _decide(time.monotonic())
                    if decision is not None:
                        if decision["accept"]:
                            top_candidate_cid, top_score_norm = decision["top"]
                            media_type, media_id = split_cid(top_candidate_cid)

                            summary = await fetch_media_summary(mongo_db, media_type, media_id)
                            result = MediaResultPayload(
                                data=StreamResponse(
                                    success=True,
                                    sessionId=self.session_id,
                                    result=MediaResult(
                                        id=media_id,
                                        title=summary.get("title") or summary.get("name"),
                                        posterUrl=summary.get("poster_path"),
                                        year=summary.get("release_date") or summary.get("first_air_date"),
                                        #director=summary.get("director"),
                                        genre=summary.get("genres", ""),
                                        description=summary.get("overview"),
                                        #trailerUrl=summary.get("trailer_url"),
                                        tmdbRating=summary.get("vote_average"),
                                        #imdbRating=summary.get("imdb_rating"),
                                        duration=summary.get("runtime"),
                                    ),
                                    confidence=top_score_norm,
                                    processingTime=time_remaining,
                                )
                            )
                            await self._result_q.put(result)
                            if stop_after_match:
                                try:
                                    await self.close()
                                except asyncio.TimeoutError:
                                    logger.warning("Timeout while closing STT task during stop_after_match")
                            return result
                        else:
                            result = MediaResultPayload(
                                data=StreamResponse(
                                    success=False,
                                    sessionId=self.session_id,
                                    error="rejected"
                                )
                            )
                            await self._result_q.put(result)
                            return result

            # graceful stop
            result = MediaResultPayload(
                data=StreamResponse(
                    success=False,
                    sessionId=self.session_id,
                    error="stopped"
                )
            )
            await self._result_q.put(result)
            return result

        except asyncio.CancelledError:
            cancelled_result = MediaResultPayload(
                data=StreamResponse(
                    success=False,
                    sessionId=self.session_id,
                    error="cancelled"
                )
            )
            await self._result_q.put(cancelled_result)
            return cancelled_result
        except Exception as e:
            logger.error(f"Error in identification pipeline {self.session_id}: {e}")
            error_result = MediaResultPayload(
                data=StreamResponse(
                    success=False,
                    sessionId=self.session_id,
                    error=str(e)
                )
            )
            await self._result_q.put(error_result)
            return error_result

    async def _flush_queue(self, timeout: float = 3.0) -> None:
        """Wait until the audio queue is empty (best-effort, bounded by timeout)."""
        deadline = asyncio.get_event_loop().time() + timeout
        while not self._audio_queue.empty() and asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(0.01)

    async def _wait_or_cancel(self, task: Optional[asyncio.Task], timeout: float = 5.0) -> None:
        """Wait for task to finish; cancel if it exceeds timeout."""
        if not task:
            return
        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        except asyncio.CancelledError:
            pass

    async def close(self) -> None:
        """Gracefully stop streaming and reset internal state for reuse."""
        # If we're already closing, ensure the task stops and reset.
        if self._closing:
            await self._wait_or_cancel(self._stt_task)
            self.reset()
            return
        self._closing = True
        try:
            try:
                await self._flush_queue()
            except asyncio.CancelledError:
                pass
            # Signal end-of-stream to the STT loop.
            await self._audio_queue.put(None)
            await self._wait_or_cancel(self._stt_task)
        finally:
            self.reset()
            self._closing = False


"""
[
    {
        "id": None,
        "metadata": {
            "_id":              "687a0a4db6786590054a7a11",
            "movie_id":         "687a0a4cb6786590054a79e9",
            "index":            39,
            "vector_score":     0.03225806451612903,
            "rank":             0,
            "fulltext_score":   0,
            "score":            0.03225806451612903
        },
        "page_content": "Example movie chunk text...",
        "type": "Document"
    },
    {
        "id": None,
        "metadata": {
            "_id":                  "6898c761d20c49476106c5f6",
            "episode_id":           "6898c761d20c49476106c5ec",
            "season_number":        1,
            "episode_number":       1,
            "index":                0,
            "tv_show_id":           "6898c761d20c49476106c5ea",
            "vector_score":         0.03225806451612903,
            "rank":                 0,
            "score":                0.07987711213517665,
            "fulltext_score":       0.047619047619047616
        },
        "page_content": "Example TV show chunk text...",
        "type": "Document"
    }
]
"""
