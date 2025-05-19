from typing import Dict, Any
from .client import TMDbClient


async def get_movie_metadata(
    client:     TMDbClient,
    movie_id:   int,
    language:   str = "en-US"
) -> Dict[str, Any]:
    """
    Fetch complete metadata for a movie including details, credits, images,
    videos, watch providers, and additional context.
    
    Args:
        client (TMDbClient): Initialized TMDB client
        movie_id (int): TMDB movie ID
        language (str, optional): Language code. Defaults to "en-US".
        
    Returns:
        Dict[str, Any]: Complete movie metadata
    """
    