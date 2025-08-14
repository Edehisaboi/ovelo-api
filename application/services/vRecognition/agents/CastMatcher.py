from typing import Dict, Any

import asyncio
from langchain_core.documents import Document

from application.services.vRecognition.utils import exception, extract_media_from_metadata
from infrastructure.database.queries import has_actors
from infrastructure.database.mongodb import MongoCollectionsManager
from application.services.vRecognition.state import State


class CastMatcher:
    def __init__(self, mongo_db: MongoCollectionsManager):
        self.mongo_db = mongo_db

    @exception
    async def execute(self, state: State):
        if not self.mongo_db:
            raise ValueError("MongoDB collections manager is not initialized.")

        actors = state.get("actors") or []
        candidates = state.get("candidates") or []

        movie_ids   = set()
        tv_ids      = set()

        for candidate, _score in candidates:
            metadata = candidate.metadata
            media_type, media_id = extract_media_from_metadata(metadata)
            if media_type == "movie" and media_id:
                movie_ids.add(media_id)
            elif media_type == "tv" and media_id:
                tv_ids.add(media_id)

        batch_results: Dict[str, Dict[str, Any]] = {}

        movie_task = has_actors(self.mongo_db, list(movie_ids), actors, "movie")
        tv_task    = has_actors(self.mongo_db, list(tv_ids),    actors, "tv")

        movie_result, tv_result = await asyncio.gather(
            movie_task, tv_task, return_exceptions=True
        )

        if not isinstance(movie_result, Exception) and isinstance(movie_result, dict):
            batch_results.update(movie_result)
        if not isinstance(tv_result, Exception) and isinstance(tv_result, dict):
            batch_results.update(tv_result)

        if isinstance(movie_result, Exception) or isinstance(tv_result, Exception):
            return {
                "error": {
                    "type": "ExecutionError",
                    "message": "Error occurred while querying actors.",
                    "node": self.__class__.__name__,
                }
            }
        return {
            "actor_matches": batch_results
        }
 

