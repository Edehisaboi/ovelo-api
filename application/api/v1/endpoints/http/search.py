import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.core.config import settings
from application.core.dependencies import mongo_manager
from application.core.logging import get_logger

from application.models import MovieDetails, TVDetails, SearchResults
from application.services.media.tmdb import tmdb_service

from application.data.generator import generate_data

from infrastructure.database import search_by_title
from infrastructure.database import hybrid_search

router = APIRouter()

logger = get_logger(__name__)


class SearchRequest(BaseModel):
    """Request model for search operations."""
    query:          str
    limit:          int
    include_movies: bool = True
    include_tv:     bool = True


class SearchResponse(BaseModel):
    """Response model for search operations."""
    query:      str
    movies:     List[MovieDetails] = []
    tv:         List[TVDetails] = []
    tmdb:       Optional[SearchResults] = None
    total:      int


class VectorSearchRequest(BaseModel):
    query: str

class VectorSearchResult(BaseModel):
    document: dict

class VectorSearchResponse(BaseModel):
    query: str
    results: list[VectorSearchResult]
    total: int


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
        db_movie, db_tv = await search_by_title(
            manager=mongodb_manager,
            query=request.query,
            limit = request.limit
        )
    except Exception as e:
        logger.error(f"Error searching database: {e}")
        raise HTTPException(status_code=500, detail="Database search failed.")

    total = (
        len(db_movie) + len(db_tv)
    )

    if (not db_movie and not db_tv) or total < request.limit:
        logger.info("No results found in database or insufficient results, falling back to TMDb API")
        try:
            tmdb_results: Optional[SearchResults] = None

            if request.include_movies and request.include_tv:
                # Will include media_type 'People' as per TMDb's multi-search capabilities
                tmdb_results = await tmdb_service.search_multi(request.query)
            elif request.include_movies:
                tmdb_results = await tmdb_service.search_movies(
                    query=request.query,
                    include_adult=True
                )
            elif request.include_tv:
                tmdb_results = await tmdb_service.search_tv_shows(
                    query=request.query,
                    include_adult=True
                )

            # Ingest TMDb results into the database if they are not already present
            # TODO: Turn to a background task
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
                movies=db_movie,
                tv=db_tv,
                tmdb=tmdb_results,
                total= total + (tmdb_results.total_results if tmdb_results else 0)
            )
        except Exception as e:
            logger.error(f"Error searching TMDb API: {e}")
            raise HTTPException(status_code=500, detail="TMDb API search failed.")

    # Database results are sufficient
    return SearchResponse(
        query=request.query,
        movies=db_movie,
        tv=db_tv,
        tmdb=None,
        total=total
    )


@router.post("/vector-search", response_model=VectorSearchResponse)
async def vector_search_endpoint(
    request: VectorSearchRequest,
    mongodb_manager = Depends(mongo_manager)
):
    """Perform a vector-based semantic search over movie and TV chunks."""
    logger.info(f"Vector search: {request.query}")

    try:
        movie_task  = hybrid_search(mongodb_manager.movie_chunks_retriever, request.query)
        tv_task     = hybrid_search(mongodb_manager.tv_chunks_retriever,    request.query)

        # run both and collect exceptions
        results = await asyncio.gather(movie_task, tv_task, return_exceptions=True)
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            for e in errors:
                logger.error(f"Sub-search failed: {e}")
            raise HTTPException(status_code=500, detail="One or more searches failed")

        combined = [doc for sublist in results for doc in sublist]

        resp_items = [VectorSearchResult(document=doc.model_dump()) for doc in combined]
        return VectorSearchResponse(
            query=request.query,
            results=resp_items,
            total=len(resp_items)
        )
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        raise HTTPException(status_code=500, detail="Vector search failed.")
