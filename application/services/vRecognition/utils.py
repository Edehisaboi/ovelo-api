from typing import Dict, Any, Tuple, Optional
import functools

import asyncio
import tiktoken
from bson import ObjectId
from bson.errors import InvalidId

from application.core.logging import get_logger
from application.core.config import settings
from infrastructure.database import MongoCollectionsManager

logger = get_logger(__name__)


def cid(media_type: str, media_id: str | int) -> str:
    return f"{media_type}:{media_id}"

def split_cid(cid_str: str) -> Tuple[str, str]:
    media_type, _, identifier = cid_str.partition(":")
    return media_type, identifier

def extract_media_from_metadata(metadata: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    if (movie_id := metadata.get("movie_id")) is not None:
        return "movie", str(movie_id)
    if (tv_id := metadata.get("tv_show_id")) is not None:
        return "tv", str(tv_id)
    return None, None

def exception(func):
    @functools.wraps(func)
    async def _aw_wrapper(state, *args, **kwargs):
        node_name = func.__name__
        try:
            return await func(state, *args, **kwargs)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"System error in {node_name}: {e}")
            return {
                "error": {
                    "type":    "systemError",
                    "node":    node_name,
                    "message": str(e)
                },
            }
    return _aw_wrapper

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
                '_id', 'images', 'credits', 'videos', 'external_ids', 'embedding', 'embedding_model',
                'tmdb_id', 'origin_country', 'spoken_languages', 'updated_at', 'created_at'
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


def is_least_percentage_of_chunk_size(text: str, percentage: float) -> bool:
    enc = tiktoken.get_encoding(settings.OPENAI_TOKEN_ENCODING)
    tokens = enc.encode(text)
    return len(tokens) >= int(settings.CHUNK_SIZE * percentage)
