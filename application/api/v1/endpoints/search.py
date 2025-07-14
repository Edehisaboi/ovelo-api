from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.core.config import settings
from application.core.resources import mongo_manager
from application.core.logging import get_logger

from application.models import MovieDetails, TVDetails, SearchResults
from application.services.media import tmdb_service

from application.data.generator import generate_data

from infrastructure.database import search_by_title

router = APIRouter()

logger = get_logger(__name__)


class SearchRequest(BaseModel):
    """Request model for search operations."""
    query:          str
    limit:          int = settings.MAX_RESULTS_PER_PAGE
    include_movies: bool = True
    include_tv:     bool = True
    exact_match:    bool = False
    language:       Optional[str] = settings.TMDB_LANGUAGE
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
    request: SearchRequest,
    mongodb_manager = Depends(mongo_manager)
):
    """
    Search for movies and TV shows using hybrid search.
    If the database returns insufficient results, fallback to the TMDb API.
    """
    logger.info(f"Searching for: {request.query}")

    try:
        # Search the database for movies and TV shows
        db_results = await search_by_title(
            manager=mongodb_manager,
            query=request.query,
            exact_match=request.exact_match,
            language=request.language,
            country=request.country,
            limit = request.limit
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
                    language=request.language or settings.TMDB_LANGUAGE,
                    include_adult=True,
                    region=request.country
                )
            elif request.include_tv:
                tmdb_results = await tmdb_service.search_tv_shows(
                    query=request.query,
                    language=request.language or settings.TMDB_LANGUAGE,
                    include_adult=True
                )

            # Ingest TMDb results into the database if they are not already present
            if settings.INGESTION_ENABLED and tmdb_results is not None:
                async for model in generate_data(tmdb_results, manager=mongodb_manager):
                    if model is not None:
                        if isinstance(model, MovieDetails):
                            await mongodb_manager.insert_movie_document(model)
                        elif isinstance(model, TVDetails):
                            await mongodb_manager.insert_tv_show_document(model)

            # Compose empty or partial DB results, but always provide query and total_results for consistency
            return SearchResponse(
                query=request.query,
                movies=db_results["movies"] if db_results else [],
                tv_shows=db_results["tv_shows"] if db_results else [],
                tmdb_search=tmdb_results,
                total_results=len(tmdb_results.results) if tmdb_results else 0,
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
