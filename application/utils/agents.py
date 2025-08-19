from typing import Dict, Any, Tuple, Optional
import functools

import asyncio
import tiktoken

from application.core.logging import get_logger
from application.core.config import settings

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
                "end": True
            }
    return _aw_wrapper

def is_least_percentage_of_chunk_size(text: str, percentage: float) -> bool:
    enc = tiktoken.get_encoding(settings.OPENAI_TOKEN_ENCODING)
    tokens = enc.encode(text)
    return len(tokens) >= int(settings.CHUNK_SIZE * percentage)
