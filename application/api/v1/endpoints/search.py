from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from application.core.dependencies import (
    get_movie_db, get_tv_db, get_embedding_client,
    get_tmdb_service, get_opensubtitles_client
)
from infrastructure.database.mongodb import MongoClientWrapper
from application.services.media.tmdb import TMDbService
from application.services.embeddings.embedding import EmbeddingService
from application.services.subtitles import opensubtitles_client
from application.models.media import MovieDetails, TVDetails, SearchResults
from application.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for search operations."""
    query: str
    search_type: str = "hybrid"  # "hybrid", "vector", "text"
    limit: int = 10
    include_movies: bool = True
    include_tv: bool = True


class SearchResponse(BaseModel):
    """Response model for search operations."""
    movies: List[MovieDetails] = []
    tv_shows: List[TVDetails] = []
    total_results: int = 0
    search_type: str
    query: str


@router.post("/search", response_model=SearchResponse)
async def search_media(
    request: SearchRequest,
    movie_db: MongoClientWrapper = Depends(get_movie_db),
    tv_db: MongoClientWrapper = Depends(get_tv_db),
    embedding_service: EmbeddingService = Depends(get_embedding_client),
    tmdb_service: TMDbService = Depends(get_tmdb_service),
    opensubtitles_client = Depends(get_opensubtitles_client)
):
    """Search for movies and TV shows using hybrid search."""
    try:
        logger.info(f"Searching for: {request.query}")
        
        movies = []
        tv_shows = []
        total_results = 0
        
        # Search movies if requested
        if request.include_movies:
            try:
                movie_results = await movie_db.vector_search(
                    query=request.query,
                    limit=request.limit
                )
                movies = [MovieDetails(**result) for result in movie_results]
                total_results += len(movies)
                logger.info(f"Found {len(movies)} movies")
            except Exception as e:
                logger.error(f"Error searching movies: {e}")
        
        # Search TV shows if requested
        if request.include_tv:
            try:
                tv_results = await tv_db.vector_search(
                    query=request.query,
                    limit=request.limit
                )
                tv_shows = [TVDetails(**result) for result in tv_results]
                total_results += len(tv_shows)
                logger.info(f"Found {len(tv_shows)} TV shows")
            except Exception as e:
                logger.error(f"Error searching TV shows: {e}")
        
        return SearchResponse(
            movies=movies,
            tv_shows=tv_shows,
            total_results=total_results,
            search_type=request.search_type,
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/movies", response_model=List[MovieDetails])
async def search_movies(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results"),
    movie_db: MongoClientWrapper = Depends(get_movie_db)
):
    """Search for movies only."""
    try:
        results = await movie_db.vector_search(
            query=query,
            limit=limit
        )
        return [MovieDetails(**result) for result in results]
    except Exception as e:
        logger.error(f"Movie search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/tv", response_model=List[TVDetails])
async def search_tv_shows(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results"),
    tv_db: MongoClientWrapper = Depends(get_tv_db)
):
    """Search for TV shows only."""
    try:
        results = await tv_db.vector_search(
            query=query,
            limit=limit
        )
        return [TVDetails(**result) for result in results]
    except Exception as e:
        logger.error(f"TV search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/tmdb", response_model=SearchResults)
async def search_tmdb(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number"),
    include_adult: bool = Query(True, description="Include adult content"),
    region: Optional[str] = Query(None, description="Region filter"),
    year: Optional[int] = Query(None, description="Year filter"),
    tmdb_service: TMDbService = Depends(get_tmdb_service)
):
    """Search TMDb API for movies and TV shows."""
    try:
        results = await tmdb_service.search_multi(
            query=query,
            page=page,
            include_adult=include_adult,
            region=region,
            year=year
        )
        return results
    except Exception as e:
        logger.error(f"TMDb search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/tmdb/movies", response_model=SearchResults)
async def search_tmdb_movies(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number"),
    include_adult: bool = Query(True, description="Include adult content"),
    region: Optional[str] = Query(None, description="Region filter"),
    year: Optional[int] = Query(None, description="Year filter"),
    tmdb_service: TMDbService = Depends(get_tmdb_service)
):
    """Search TMDb API for movies only."""
    try:
        results = await tmdb_service.search_movies(
            query=query,
            page=page,
            include_adult=include_adult,
            region=region,
            year=year
        )
        return results
    except Exception as e:
        logger.error(f"TMDb movie search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/tmdb/tv", response_model=SearchResults)
async def search_tmdb_tv(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number"),
    include_adult: bool = Query(True, description="Include adult content"),
    tmdb_service: TMDbService = Depends(get_tmdb_service)
):
    """Search TMDb API for TV shows only."""
    try:
        results = await tmdb_service.search_tv_shows(
            query=query,
            page=page,
            include_adult=include_adult
        )
        return results
    except Exception as e:
        logger.error(f"TMDb TV search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 