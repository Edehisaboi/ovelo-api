from __future__ import annotations

from datetime import datetime, timezone

from application.core.logging import get_logger
from application.services.vRecognition.state import State, Match
from application.utils.agents import exception
from infrastructure.database.mongodb import MongoCollectionsManager
from infrastructure.database.queries import fetch_media_summary

logger = get_logger(__name__)


class Metadata:
    def __init__(self, mongo_db: MongoCollectionsManager) -> None:
        self.mongo_db: MongoCollectionsManager = mongo_db

    @exception
    async def extract(self, state: State):
        if not state["match"]:
            return {}

        match: Match = state["match"]
        media_type, media_id = match.get("type"), match.get("id")

        summary = await fetch_media_summary(self.mongo_db, media_type, media_id)
        if not summary:
            return {}

        return {
            "metadata": {
                "type": "result",
                "data": {
                    "success": True,
                    "sessionId": "default",
                    "result": {
                        "id":          media_id,
                        "title":       summary.get("title") or summary.get("name"),
                        "posterUrl":   summary.get("poster_path"),
                        "year":        summary.get("release_date") or summary.get("first_air_date"),
                        "genre":       summary.get("genres", ""),
                        "description": summary.get("overview"),
                        "tmdbRating":  summary.get("vote_average"),
                        "duration":    summary.get("runtime"),
                        "identifiedAt": datetime.now(timezone.utc).isoformat()
                    },
                }
            }
        }

