from typing import Optional
from .client import TMDbClient
from .models import SearchResults

async def search_media(
    client:         TMDbClient,
    query:          str,
    page:           int = 1,
    language:       str = "en-US",
    include_adult:  bool = False,
    region:         Optional[str] = None,
    year:           Optional[int] = None
) -> SearchResults:
    """
    Search for movies and TV shows using TMDB API.
    
    Args:
        client (TMDbClient): Initialized TMDB client
        query (str): The search query string
        page (int, optional): Page number for pagination. Defaults to 1.
        language (str, optional): Language code for results. Defaults to "en-US".
        include_adult (bool, optional): Include adult content. Defaults to False.
        region (str, optional): Region code for results. Defaults to None.
        year (int, optional): Filter by year. Defaults to None.
    
    Returns:
        SearchResults: Search results containing movies and TV shows
        
    Raises:
        httpx.HTTPError: If the API request fails
    """
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
    year:               Optional[int] = None,
    primary_release_year: Optional[int] = None
) -> SearchResults:
    """
    Search for movies only using TMDB API.
    
    Args:
        client (TMDbClient): Initialized TMDB client
        query (str): The search query string
        page (int, optional): Page number for pagination. Defaults to 1.
        language (str, optional): Language code for results. Defaults to "en-US".
        include_adult (bool, optional): Include adult content. Defaults to False.
        region (str, optional): Region code for results. Defaults to None.
        year (int, optional): Filter by year. Defaults to None.
        primary_release_year (int, optional): Filter by primary release year. Defaults to None.
    
    Returns:
        SearchResults: Search results containing only movies
        
    Raises:
        httpx.HTTPError: If the API request fails
    """
    return await client.search.movies(
        query=query,
        page=page,
        language=language,
        include_adult=include_adult,
        region=region,
        year=year,
        primary_release_year=primary_release_year
    )

async def search_tv_shows(
    client:             TMDbClient,
    query:              str,
    page:               int = 1,
    language:           str = "en-US",
    include_adult:      bool = False,
    first_air_date_year: Optional[int] = None
) -> SearchResults:
    """
    Search for TV shows only using TMDB API.
    
    Args:
        client (TMDbClient): Initialized TMDB client
        query (str): The search query string
        page (int, optional): Page number for pagination. Defaults to 1.
        language (str, optional): Language code for results. Defaults to "en-US".
        include_adult (bool, optional): Include adult content. Defaults to False.
        first_air_date_year (int, optional): Filter by first air date year. Defaults to None.
    
    Returns:
        SearchResults: Search results containing only TV shows
        
    Raises:
        httpx.HTTPError: If the API request fails
    """
    return await client.search.tv_shows(
        query=query,
        page=page,
        language=language,
        include_adult=include_adult,
        first_air_date_year=first_air_date_year
    )

__all__ = ['search_media', 'search_movies', 'search_tv_shows']
