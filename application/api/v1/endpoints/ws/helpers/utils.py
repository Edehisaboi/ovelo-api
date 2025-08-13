from typing import Dict, Any, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId

from infrastructure.database.mongodb import MongoCollectionsManager

def cid(media_type: str, media_id: str) -> str:
    return f"{media_type}:{media_id}"

def split_cid(cid_str: str) -> Tuple[str, str]:
    media_type, _, identifier = cid_str.partition(":")
    return media_type, identifier

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return default

def extract_media_from_metadata(metadata: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    if (movie_id := metadata.get("movie_id")) is not None:
        return "movie", str(movie_id)
    if (tv_id := metadata.get("tv_show_id")) is not None:
        return "tv", str(tv_id)
    return None, None

async def fetch_media_summary(
    mongo_db:   MongoCollectionsManager,
    media_type: str,
    media_id:   str
) -> Dict[str, Any]:
    try:
        object_id = ObjectId(media_id)
    except InvalidId:
        return {}

    if media_type == "movie":
        coll = mongo_db.movies.collection
    elif media_type == "tv":
        coll = mongo_db.tv_shows.collection
    else:
        raise ValueError("media must be 'movie' or 'tv'")

    pipeline = [
        {
            '$match': {
                '_id': object_id,
            }
        }, {
            '$unset': [
                '_id', 'images', 'credits', 'videos', 'external_ids', 'embedding', 'embedding_model', 'tmdb_id', 'origin_country', 'spoken_languages', 'updated_at', 'created_at'
            ]
        }, {
            '$limit': 1
        }
    ]

    cursor = coll.aggregate(pipeline)
    doc = await anext(cursor, None)
    if doc and "genres" in doc:
        # Join all genre names with '|'
        doc["genres"] = " | ".join(g["name"] for g in doc["genres"] if "name" in g)
    return doc or {}

async def notify_update(on_update, payload: dict) -> None:
    if not on_update:
        return
    try:
        await on_update(payload)
    except Exception as e:
        # Log upstream to avoid silent failures if desired; here we no-op
        _ = e
        return