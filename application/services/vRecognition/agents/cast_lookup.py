from __future__ import annotations
from typing import Dict, Any, List, Set, Sequence, cast

import asyncio

from application.core.logging import get_logger
from application.utils.agents import exception, extract_media_from_metadata
from application.services.vRecognition.state import State
from infrastructure.database.queries import matched_actors
from infrastructure.database.mongodb import MongoCollectionsManager

logger = get_logger(__name__)


class CastLookup:
    """Annotate candidates with matched actor names, cached per actor signature.
    Cache semantics:
    - Cache key: media_id (movie/tv), value: List[str] of matched actor names (possibly []).
    - Cache is scoped to the current actor signature (order-insensitive set of actors).
    Concurrency:
    - An asyncio lock protects cache/signature updates when execute() is called concurrently."""

    def __init__(self, mongo_db: MongoCollectionsManager) -> None:
        self.mongo_db: MongoCollectionsManager = mongo_db
        self._sig: frozenset[str] = frozenset()
        self._cache: Dict[str, List[str]] = {}   # media_id -> matched names (possibly [])
        self._cached_ids: Set[str] = set()
        self._lock = asyncio.Lock()

    def _reset_cache_for_signature(self, actors: List[str]) -> None:
        signature = frozenset(actors)
        if signature != self._sig:
            self._sig = signature
            self._cache.clear()
            self._cached_ids.clear()

    def _apply_cached_mathes(self, candidates: List[Dict[str, Any]]) -> None:
        for doc in candidates:
            md = doc.get("metadata") or {}
            media_type, media_id = extract_media_from_metadata(md)
            if not media_type or not media_id:
                continue
            matched = self._cache.get(media_id, [])
            if "metadata" not in doc or doc["metadata"] is None:
                doc["metadata"] = {}
            doc["metadata"]["matched_cast"] = matched

    @staticmethod
    def _collect_ids_by_type(candidates: Sequence[Any]) -> tuple[Set[str], Set[str]]:
        movie_ids: Set[str] = set()
        tv_ids: Set[str] = set()
        for item in candidates or []:
            md = item.get("metadata") if isinstance(item, dict) else None
            media_type, media_id = extract_media_from_metadata(md or {})
            if media_type == "movie" and media_id:
                movie_ids.add(media_id)
            elif media_type == "tv" and media_id:
                tv_ids.add(media_id)
        return movie_ids, tv_ids

    @exception
    async def annotate_candidates(self, state: State) -> Dict[str, Any]:
        if not self.mongo_db:
            raise ValueError("MongoDB collections manager is not initialized.")

        actors: List[str] = state.get("actors") or []
        candidates = cast(List[Dict[str, Any]], state.get("candidates") or [])
        if not candidates or not actors:
            return {"candidates": candidates}

        async with self._lock:
            self._reset_cache_for_signature(actors)

            movie_ids, tv_ids = self._collect_ids_by_type(candidates)
            movie_ids_to_query = [i for i in movie_ids if i not in self._cached_ids]
            tv_ids_to_query = [i for i in tv_ids if i not in self._cached_ids]

            if not movie_ids_to_query and not tv_ids_to_query:
                self._apply_cached_mathes(candidates)
                return {"candidates": candidates}

            encountered_error = False
            res_movie: Dict[str, List[str]] = {}
            res_tv: Dict[str, List[str]] = {}

            # Run queries concurrently when both are needed
            movie_task = matched_actors(self.mongo_db, movie_ids_to_query, actors, "movie") if movie_ids_to_query else None
            tv_task    = matched_actors(self.mongo_db, tv_ids_to_query, actors, "tv") if tv_ids_to_query else None

            try:
                if movie_task and tv_task:
                    r_movie, r_tv = await asyncio.gather(movie_task, tv_task, return_exceptions=True)
                    if isinstance(r_movie, Exception):
                        encountered_error = True
                        logger.error(f"CastLookup matched_actors(movie) error: {r_movie}")
                    else:
                        res_movie = r_movie or {}
                    if isinstance(r_tv, Exception):
                        encountered_error = True
                        logger.error(f"CastLookup matched_actors(tv) error: {r_tv}")
                    else:
                        res_tv = r_tv or {}
                elif movie_task:
                    res_movie = await movie_task
                elif tv_task:
                    res_tv = await tv_task
            except Exception as e:
                encountered_error = True
                logger.error(f"CastLookup matched_actors concurrent error: {e}")

            # Update cache with returned mappings (covers all requested ids; may be empty lists)
            for mid, matched in res_movie.items():
                self._cache[mid] = matched or []
                self._cached_ids.add(mid)
            for tid, matched in res_tv.items():
                self._cache[tid] = matched or []
                self._cached_ids.add(tid)

            # Annotate candidates in place
            self._apply_cached_mathes(candidates)

        if encountered_error:
            return {
                "candidates": candidates,
                "error": {
                    "type": "systemError",
                    "message": "Error looking up matched cast (partial results applied).",
                    "node": self.__class__.__name__,
                },
            }

        return {"candidates": candidates}
