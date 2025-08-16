from typing import Dict, Any

import asyncio

from application.services.vRecognition.utils import exception, extract_media_from_metadata
from infrastructure.database.queries import has_actors
from infrastructure.database.mongodb import MongoCollectionsManager
from application.services.vRecognition.state import State


class CastMatcher:
    def __init__(self, mongo_db: MongoCollectionsManager):
        self.mongo_db = mongo_db
        self._last_sig: tuple[str, ...] = ()
        self._last_ids: set[str] = set()
        self._last_result: Dict[str, Dict[str, Any]] = {}

    @exception
    async def execute(self, state: State):
        if not self.mongo_db:
            raise ValueError("MongoDB collections manager is not initialized.")

        actors = state.get("actors") or []
        candidates = state.get("candidates") or []
        if not actors or not candidates:
            return {"actor_matches": {}}

        movie_ids, tv_ids = set(), set()
        for doc, _ in candidates:
            media_type, media_id = extract_media_from_metadata(doc.metadata)
            if media_type == "movie" and media_id:
                movie_ids.add(media_id)
            elif media_type == "tv" and media_id:
                tv_ids.add(media_id)

        sig = tuple(sorted(a.strip() for a in actors))
        ids_now = set().union(movie_ids, tv_ids)

        # if nothing changed, return cached result
        if sig == self._last_sig and ids_now.issubset(self._last_ids):
            return {"actor_matches": {k: v for k, v in self._last_result.items() if k in ids_now}}

        movie_task = has_actors(self.mongo_db, list(movie_ids), actors, "movie")
        tv_task    = has_actors(self.mongo_db, list(tv_ids),    actors, "tv")
        movie_result, tv_result = await asyncio.gather(
            movie_task, tv_task, return_exceptions=True
        )

        batch: Dict[str, Dict[str, Any]] = {}
        if not isinstance(movie_result, Exception) and isinstance(movie_result, dict):
            batch.update(movie_result)
        if not isinstance(tv_result, Exception) and isinstance(tv_result, dict):
            batch.update(tv_result)

        if isinstance(movie_result, Exception) or isinstance(tv_result, Exception):
            return {
                "error": {
                    "type": "systemError",
                    "message": "Error querying actors.",
                    "node": self.__class__.__name__,
                }
            }

        # Cache & return only for current ids
        self._last_sig = sig
        self._last_ids |= ids_now
        self._last_result.update(batch)

        return {
            "actor_matches": batch
        }
 

