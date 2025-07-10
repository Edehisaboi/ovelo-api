from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.core.config import settings
from application.core.resources import movie_db, tv_db
from application.core.logging import get_logger

from application.models.media import MovieDetails, TVDetails, SearchResults
from application.services.media import tmdb_service

from infrastructure.database.mongodb import MongoClientWrapper
from infrastructure.database.queries import search_by_title

router = APIRouter()

logger = get_logger(__name__)


class SearchRequest(BaseModel):
    """Request model for search operations."""
    query:          str
    limit:          int = settings.MAX_RESULTS_PER_PAGE
    include_movies: bool = True
    include_tv:     bool = True
    exact_match:    bool = False
    language:       Optional[str] = None
    country:        Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for search operations."""
    query:          str
    movies:         List[MovieDetails]
    tv_shows:       List[TVDetails]
    tmdb_search:    Optional[SearchResults] = None
    total_results:  int


@router.post("/search", response_model=SearchResponse)
async def search_media(
    request:         SearchRequest,
    movie_db_client: MongoClientWrapper = Depends(movie_db),
    tv_db_client:    MongoClientWrapper = Depends(tv_db)
):
    """
    Search for movies and TV shows using hybrid search.
    If the database returns insufficient results, fallback to the TMDb API.
    """
    logger.info(f"Searching for: {request.query}")

    try:
        db_results = search_by_title(
            movie_db=movie_db_client,
            tv_db=tv_db_client,
            query=request.query,
            exact_match=request.exact_match,
            language=request.language,
            country=request.country,
            limit=request.limit
        )
    except Exception as e:
        logger.error(f"Error searching database: {e}")
        raise HTTPException(status_code=500, detail="Database search failed.")

    total_db_results = (
        len(db_results["movies"]) +
        len(db_results["tv_shows"])
        if db_results else 0
    )

    if not db_results or total_db_results < request.limit:
        logger.info("No results found in database or insufficient results, falling back to TMDb API.")
        try:
            tmdb_results: Optional[SearchResults] = None

            if request.include_movies and request.include_tv:
                # Will include media_type 'People' as per TMDb's multi-search capabilities
                tmdb_results = await tmdb_service.search_multi(request.query)
            elif request.include_movies:
                tmdb_results = await tmdb_service.search_movies(
                    query=request.query,
                    language=request.language,
                    include_adult=True,
                    region=request.country
                )
            elif request.include_tv:
                tmdb_results = await tmdb_service.search_tv_shows(
                    query=request.query,
                    language=request.language,
                    include_adult=True
                )

            # Compose empty or partial DB results, but always provide query and total_results for consistency
            return SearchResponse(
                query=request.query,
                movies=db_results["movies"],
                tv_shows=db_results["tv_shows"],
                tmdb_search=tmdb_results,
                total_results=len(tmdb_results.results),
            )
        except Exception as e:
            logger.error(f"Error searching TMDb API: {e}")
            raise HTTPException(status_code=500, detail="TMDb API search failed.")

    # Database results are sufficient
    return SearchResponse(
        query=request.query,
        movies=db_results["movies"],
        tv_shows=db_results["tv_shows"],
        tmdb_search=None,
        total_results=total_db_results
    )
