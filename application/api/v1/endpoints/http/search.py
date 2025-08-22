from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from application.core.config import settings
from application.core.dependencies import mongo_manager
from application.core.logging import get_logger

from application.services.vRecognition.state import MediaResult
from application.models import SearchResult, SearchResults
from application.services.media.tmdb import tmdb_service

from infrastructure.database import search_by_title

router = APIRouter()

logger = get_logger(__name__)


class SearchRequest(BaseModel):
    """Request model for search operations."""
    query:  str
    type:   str = "all"  # "all", "movie", "tv"
    limit:  int = 10


class SearchResponse(BaseModel):
    """Response model for search operations."""
    success: bool = True
    results: List[MediaResult] = []
    total:   int = 0
    page:    int = 1
    hasMore: Optional[bool] = False
    error:   Optional[str] = None

@router.post("/search/videos", response_model=SearchResponse)
async def search_media(
    request: SearchRequest,
    mongodb_manager = Depends(mongo_manager)
):
    logger.info(f"Searching for: {request.query}")

    # Determine what to include based on type
    include_movies = request.type in ["all", "movie"]
    include_tv = request.type in ["all", "tv"]

    try:
        # Search the database for movies and TV shows
        db_results = await search_by_title(
            manager=mongodb_manager,
            query=request.query,
            limit=request.limit
        )
    except Exception as e:
        logger.error(f"Error searching database: {e}")
        return SearchResponse(
            success=False,
            error="Database search failed."
        )

    total_db_results = len(db_results)
    has_more = total_db_results >= request.limit

    # If insufficient results, fallback to TMDb API
    if total_db_results < request.limit:
        logger.info("Insufficient results in database, falling back to TMDb API")
        try:
            tmdb_results: Optional[SearchResults] = None

            if include_movies and include_tv:
                tmdb_results = await tmdb_service.search_multi(request.query)
            elif include_movies:
                tmdb_results = await tmdb_service.search_movies(
                    query=request.query,
                    include_adult=True
                )
            elif include_tv:
                tmdb_results = await tmdb_service.search_tv_shows(
                    query=request.query,
                    include_adult=True
                )

            if tmdb_results:
                # Add TMDb results to the list
                for result in tmdb_results.results:
                    if result:
                        db_results.append(result)
                
                # Update total and has_more
                total_db_results = len(db_results)
                has_more = total_db_results >= request.limit

        except Exception as e:
            logger.error(f"Error searching TMDb API: {e}")
            return SearchResponse(
                success=False,
                error="TMDb API search failed."
            )

    # Format results for client response
    formatted_results = []
    for result in db_results[:request.limit]:
        formatted_item = _format_search_result(result)
        formatted_results.append(formatted_item)

    return SearchResponse(
        success=True,
        results=formatted_results,
        total=len(formatted_results),
        page=1,
        hasMore=has_more
    )


def _format_search_result(search_result: SearchResult) -> MediaResult:
    """Format a SearchResult into the client-expected SearchResultItem format."""
    return MediaResult(
        id=str(search_result.tmdb_id),
        title=search_result.title or search_result.name or "Unknown",
        posterUrl=f"{settings.TMDB_IMAGE_BASE_URL}{search_result.poster_path}",
        year=str(search_result.release_date) or str(search_result.first_air_date),
        director=None,
        genre=search_result.genres or "Unknown",
        duration=None,
        description=search_result.overview,
        trailerUrl=search_result.trailer_link,
        tmdbRating=search_result.vote_average,
        imdbRating=None,
        identifiedAt=datetime.now(timezone.utc).isoformat(),
        source=None
    )