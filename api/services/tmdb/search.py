from typing import Optional
from api.clients import TMDbClient
from .model import SearchResults

async def search_media(
    client:         TMDbClient,
    query:          str,
    page:           int = 1,
    language:       str = "en-US",
    include_adult:  bool = False,
    region:         Optional[str] = None,
    year:           Optional[int] = None
) -> SearchResults:
    """Search for movies and TV shows using TMDB API."""
    return await client.search.multi(
        query=query,
        page=page,
        language=language,
        include_adult=include_adult,
        region=region,
        year=year
    )

async def search_movies(
    client:             TMDbClient,
    query:              str,
    page:               int = 1,
    language:           str = "en-US",
    include_adult:      bool = False,
    region:             Optional[str] = None,
    year:               Optional[int] = None
) -> SearchResults:
    """Search for movies only using TMDB API."""
    return await client.search.movies(
        query=query,
        page=page,
        language=language,
        include_adult=include_adult,
        region=region,
        year=year
    )

async def search_tv_shows(
    client:             TMDbClient,
    query:              str,
    page:               int = 1,
    language:           str = "en-US",
    include_adult:      bool = False
) -> SearchResults:
    """Search for TV shows only using TMDB API."""
    return await client.search.tv_shows(
        query=query,
        page=page,
        language=language,
        include_adult=include_adult
    )
