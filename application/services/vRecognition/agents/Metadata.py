from datetime import datetime, timezone

from application.core.logging import get_logger
from infrastructure.database.mongodb import MongoCollectionsManager
from application.services.vRecognition.utils import exception, split_cid, fetch_media_summary
from application.services.vRecognition.state import State

logger = get_logger(__name__)


class Metadata:
    def __init__(self, mongo_db: MongoCollectionsManager):
        self.mongo_db = mongo_db

    @exception
    async def extract(self, state: State):
        if not state["match"]:
            return {}

        match: str = state["match"]
        media_type, media_id = split_cid(match)

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

