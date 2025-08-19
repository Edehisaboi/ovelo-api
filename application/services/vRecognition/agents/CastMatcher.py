from __future__ import annotations
from typing import Dict, Any, List, Tuple, Set, Sequence, cast

import asyncio
from langchain_core.documents import Document

from application.core.logging import get_logger
from application.utils.agents import exception, extract_media_from_metadata
from application.services.vRecognition.state import State
from infrastructure.database.queries import has_actors, matched_actors
from infrastructure.database.mongodb import MongoCollectionsManager

logger = get_logger(__name__)


def _collect_ids_by_type(candidates: Sequence[Any]) -> tuple[Set[str], Set[str]]:
    """Return separate sets of movie and TV ids from candidate documents."""
    movie_ids: Set[str] = set()
    tv_ids: Set[str] = set()
    for item in candidates or []:
        doc: Document
        if isinstance(item, tuple):
            # (Document, score)
            doc = item[0]
        else:
            doc = item  # type: ignore[assignment]
        media_type, media_id = extract_media_from_metadata(doc.metadata)
        if media_type == "movie" and media_id:
            movie_ids.add(media_id)
        elif media_type == "tv" and media_id:
            tv_ids.add(media_id)
    return movie_ids, tv_ids


class CastMatcher:
    """Compute presence info per id with caching by actor signature.

    Output format: { id: { 'exists': bool, 'missing': [names...] } }
    """

    def __init__(self, mongo_db: MongoCollectionsManager) -> None:
        self.mongo_db: MongoCollectionsManager = mongo_db
        self._last_sig: tuple[str, ...] = ()
        self._last_ids: Set[str] = set()
        self._last_result: Dict[str, Dict[str, Any]] = {}

    @exception
    async def execute(self, state: State) -> Dict[str, Any]:
        if not self.mongo_db:
            raise ValueError("MongoDB collections manager is not initialized.")

        actors: List[str] = state.get("actors") or []
        candidates = cast(List[Tuple[Document, float]], state.get("candidates") or [])
        if not actors or not candidates:
            return {"actor_matches": {}}

        # Signature is unique-sorted actor list (stable cache key)
        actor_signature = tuple(sorted(set(actors)))
        movie_ids, tv_ids = _collect_ids_by_type(candidates)
        requested_ids = movie_ids | tv_ids

        # If unchanged and all ids are covered, serve from cache subset
        if actor_signature == self._last_sig and requested_ids.issubset(self._last_ids):
            return {"actor_matches": {k: v for k, v in self._last_result.items() if k in requested_ids}}

        # Query both; each returns {} if ids are empty
        movie_coro = has_actors(self.mongo_db, list(movie_ids), actors, "movie")
        tv_coro = has_actors(self.mongo_db, list(tv_ids), actors, "tv")

        batch: Dict[str, Dict[str, Any]] = {}
        encountered_error = False
        res_movie, res_tv = await asyncio.gather(movie_coro, tv_coro, return_exceptions=True)

        if isinstance(res_movie, Exception):
            encountered_error = True
            logger.error(f"CastMatcher has_actors(movie) error: {res_movie}")
        else:
            batch.update(cast(Dict[str, Dict[str, Any]], res_movie) or {})

        if isinstance(res_tv, Exception):
            encountered_error = True
            logger.error(f"CastMatcher has_actors(tv) error: {res_tv}")
        else:
            batch.update(cast(Dict[str, Dict[str, Any]], res_tv) or {})

        # Update cache
        self._last_sig = actor_signature
        self._last_ids |= requested_ids
        self._last_result.update(batch)

        out = {k: v for k, v in batch.items() if k in requested_ids}
        if encountered_error:
            return {
                "actor_matches": out,
                "error": {
                    "type": "systemError",
                    "message": "Error querying actors (partial results returned).",
                    "node": self.__class__.__name__,
                },
            }
        return {"actor_matches": out}


class CastLookup:
    """Annotate candidates with matched actor names, cached per actor signature."""

    def __init__(self, mongo_db: MongoCollectionsManager) -> None:
        self.mongo_db: MongoCollectionsManager = mongo_db
        self._sig: tuple[str, ...] = ()
        self._cache: Dict[str, List[str]] = {}   # id -> matched list
        self._cached_ids: Set[str] = set()

    def _reset_cache_if_needed(self, actors: List[str]) -> None:
        signature = tuple(sorted(set(actors)))
        if signature != self._sig:
            self._sig = signature
            self._cache.clear()
            self._cached_ids.clear()

    def _apply_to_candidates(self, candidates: List[Document]) -> None:
        for doc in candidates:
            media_type, media_id = extract_media_from_metadata(doc.metadata)
            if not media_type or not media_id:
                continue
            matched = self._cache.get(media_id, [])
            metadata = doc.metadata or {}
            metadata["matched_cast"] = matched
            doc.metadata = metadata

    @exception
    async def execute(self, state: State) -> Dict[str, Any]:
        if not self.mongo_db:
            raise ValueError("MongoDB collections manager is not initialized.")

        actors: List[str] = state.get("actors") or []
        candidates = cast(List[Document], state.get("candidates") or [])
        if not candidates or not actors:
            return {"candidates": candidates}

        # Reset cache if actor list changed -> forces re-query of all ids
        self._reset_cache_if_needed(actors)

        movie_ids, tv_ids = _collect_ids_by_type(candidates)

        # For same signature, only query ids we don't have
        movie_ids_to_query = [media_id for media_id in movie_ids if media_id not in self._cached_ids]
        tv_ids_to_query = [media_id for media_id in tv_ids if media_id not in self._cached_ids]

        # Always run both (each returns {} if empty lists)
        movie_coro = matched_actors(self.mongo_db, movie_ids_to_query, actors, "movie")
        tv_coro = matched_actors(self.mongo_db, tv_ids_to_query, actors, "tv")

        encountered_error = False
        res_movie, res_tv = await asyncio.gather(movie_coro, tv_coro, return_exceptions=True)

        if isinstance(res_movie, Exception):
            encountered_error = True
            logger.error(f"CastLookup matched_actors(movie) error: {res_movie}")
            res_movie = {}
        if isinstance(res_tv, Exception):
            encountered_error = True
            logger.error(f"CastLookup matched_actors(tv) error: {res_tv}")
            res_tv = {}

        # Update cache with results for this signature
        for key, matched in cast(Dict[str, List[str]], (res_movie or {})).items():
            self._cache[key] = matched or []
            self._cached_ids.add(key)
        for key, matched in cast(Dict[str, List[str]], (res_tv or {})).items():
            self._cache[key] = matched or []
            self._cached_ids.add(key)

        # Annotate candidates in place
        self._apply_to_candidates(candidates)

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
