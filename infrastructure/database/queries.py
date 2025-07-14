from __future__ import annotations
from typing import List, Dict, Tuple, Optional, Union

from langchain_core.documents import Document
from application.core.config import settings
from application.core.logging import get_logger
from infrastructure.database import MongoCollectionsManager, CollectionWrapper
from application.models.media import MovieDetails, TVDetails

logger = get_logger(__name__)

async def search_by_title(
    manager:        MongoCollectionsManager,
    query:          str,
    exact_match:    bool = False,
    language:       Optional[str] = None,
    country:        Optional[str] = None,
    limit: int = settings.MAX_RESULTS_PER_PAGE
) -> Dict[str, List]:
    """
    Search both movies and TV shows collections using MongoDB's $unionWith aggregation.

    Args:
        manager (MongoCollectionsManager): The MongoDB collections manager.
        query (str): The search query.
        exact_match (bool): If True, uses exact match, otherwise text search.
        language (Optional[str]): Filter by spoken language.
        country (Optional[str]): Filter by origin country.
        limit (int): Max number of results to return.

    Returns:
        Dict[str, List]: Dictionary with 'movies' and 'tv_shows' keys.
    """
    try:
        # Build match stages for movies and TV shows
        movie_match = {}
        tv_match = {}

        if exact_match:
            movie_match["$or"] = [{"title": query}, {"original_title": query}]
            tv_match["$or"] = [{"name": query}, {"original_name": query}]
        else:
            movie_match["$text"] = {"$search": query}
            tv_match["$text"] = {"$search": query}

        if language:
            movie_match["spoken_languages"] = {"$elemMatch": {"name": language}}
            tv_match["spoken_languages"] = {"$elemMatch": {"name": language}}
        if country:
            movie_match["origin_country"] = country
            tv_match["origin_country"] = country

        pipeline = [{"$match": movie_match}]
        if not exact_match:
            pipeline.append({"$addFields": {"score": {"$meta": "textScore"}}})
        pipeline.append({"$addFields": {"media_type": "movie"}})

        # TV shows sub-pipeline
        tv_pipeline = [{"$match": tv_match}]
        if not exact_match:
            tv_pipeline.append({"$addFields": {"score": {"$meta": "textScore"}}})
        tv_pipeline.append({"$addFields": {"media_type": "tv_show"}})

        pipeline.append({
            "$unionWith": {
                "coll": manager.tv_shows.collection_name,
                "pipeline": tv_pipeline
            }
        })

        # Sorting and limiting
        if not exact_match:
            pipeline.append({"$sort": {"score": -1}})
        else:
            pipeline.append({
                "$addFields": {
                    "sort_order": {
                        "$cond": {
                            "if": {"$eq": ["$media_type", "movie"]},
                            "then": 1,
                            "else": 2
                        }
                    }
                }
            })
            pipeline.append({"$sort": {"sort_order": 1}})
        pipeline.append({"$limit": limit})

        # Execute aggregation
        results = []
        async for result in manager.movies.collection.aggregate(pipeline):
            results.append(result)

        movies: List[MovieDetails] = []
        tv_shows: List[TVDetails] = []

        for result in results:
            result.pop("score", None)
            result.pop("sort_order", None)
            if "watch_providers" in result:
                result["watch/providers"] = result.pop("watch_providers")
            if "tmdb_id" in result:
                result["id"] = result.pop("tmdb_id")

            if result.get("media_type") == "movie":
                try:
                    movies.append(MovieDetails(**result))
                except Exception as e:
                    logger.warning(f"Failed to convert movie result to MovieDetails: {e}")
            else:
                try:
                    tv_shows.append(TVDetails(**result))
                except Exception as e:
                    logger.warning(f"Failed to convert TV result to TVDetails: {e}")
        return {"movies": movies, "tv_shows": tv_shows}
    except Exception as e:
        logger.error(f"Error searching both collections: {str(e)}")
        raise

async def vector_search(
    wrapper:    CollectionWrapper,
    query:      str,
    limit:      int = settings.MAX_RESULTS_PER_PAGE,
    filter_criteria: Optional[Dict] = None
) -> Union[List[Tuple[Document, float]], List[Document]]:
    """
    Perform a hybrid vector and text search using the collection's hybrid retriever.

    Args:
        wrapper (CollectionWrapper): Collection wrapper with an initialized retriever.
        query (str): The search query.
        limit (int, optional): Max number of results to return.
        filter_criteria (dict, optional): MongoDB pre_filter for vector search (if supported).

    Returns:
        Union[List[Tuple[Document, float]], List[Document]]:
            - List of (Document, score) tuples if using similarity_search_with_score.
            - List of Document if using retriever.invoke.
    """
    try:
        retriever = getattr(wrapper, "retriever", None)
        if not retriever:
            raise ValueError(
                "Hybrid search retriever not initialized for this collection."
            )
        vectorstore = retriever.vectorstore

        if vectorstore:
            # Returns List[Tuple[Document, float]]
            documents = await vectorstore.asimilarity_search_with_score(
                query=query,
                k=limit,
                pre_filter=filter_criteria
            )
        else:
            # Returns List[Document]
            documents = await retriever.ainvoke(query)

        return documents

    except Exception as e:
        logger.error(f"Error performing vector search: {e}")
        raise
