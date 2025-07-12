from __future__ import annotations
from typing import List, Dict, Tuple, Optional, Union

from langchain_core.documents import Document

from application.core.config import settings
from application.core.logging import get_logger
from infrastructure.database import MongoClientWrapper
from application.models.media import MovieDetails, TVDetails

logger = get_logger(__name__)


async def search_by_title(
    movie_db:   MongoClientWrapper,
    tv_db:      MongoClientWrapper,
    query:       str,
    exact_match: bool = False,
    language:    Optional[str] = None,
    country:     Optional[str] = None,
    limit:       int = settings.MAX_RESULTS_PER_PAGE
) -> Dict[str, List]:
    """
    Search both movies and TV shows collections using MongoDB's $unionWith aggregation.

    Returns:
        Dict[str, List]: Dictionary with 'movies' and 'tv_shows' keys containing MovieDetails and TVDetails objects.
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
            # Use $elemMatch if spoken_languages is an array of objects
            movie_match["spoken_languages"] = {"$elemMatch": {"name": language}}
            tv_match["spoken_languages"] = {"$elemMatch": {"name": language}}
        if country:
            movie_match["origin_country"] = country
            tv_match["origin_country"] = country

        # Construct the aggregation pipeline
        pipeline = [
            {"$match": movie_match},
        ]
        if not exact_match:
            pipeline.append({"$addFields": {"score": {"$meta": "textScore"}}})
        pipeline.append({"$addFields": {"media_type": "movie"}})

        # Build sub-pipeline for TV shows
        tv_pipeline = [
            {"$match": tv_match},
        ]
        if not exact_match:
            tv_pipeline.append({"$addFields": {"score": {"$meta": "textScore"}}})
        tv_pipeline.append({"$addFields": {"media_type": "tv_show"}})

        pipeline.append({
            "$unionWith": {
                "coll": tv_db.collection_name,
                "pipeline": tv_pipeline
            }
        })

        # Add sorting and limiting
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
        
        # Add limit stage
        pipeline.append({"$limit": limit})

        # Execute the aggregation asynchronously
        results = []
        async for result in movie_db.collection.aggregate(pipeline):
            results.append(result)

        # Separate results into movies and tv_shows
        movies:     List[MovieDetails] = []
        tv_shows:   List[TVDetails] = []

        for result in results:
            result.pop("score", None)
            result.pop("sort_order", None)
            
            #TODO: Fix field alias mismatch: convert watch_providers to watch/providers
            if "watch_providers" in result:
                result["watch/providers"] = result.pop("watch_providers")

            if "tmdb_id" in result:
                result["id"] = result.pop("tmdb_id")
            
            if result.get("media_type") == "movie":
                # Convert to MovieDetails object
                try:
                    movie_details = MovieDetails(**result)
                    movies.append(movie_details)
                except Exception as e:
                    logger.warning(f"Failed to convert movie result to MovieDetails: {e}")
                    # Skip invalid results
                    continue
            else:
                # Convert to TVDetails object
                try:
                    tv_details = TVDetails(**result)
                    tv_shows.append(tv_details)
                except Exception as e:
                    logger.warning(f"Failed to convert TV result to TVDetails: {e}")
                    # Skip invalid results
                    continue
        return {"movies": movies, "tv_shows": tv_shows}

    except Exception as e:
        logger.error(f"Error searching both collections: {str(e)}")
        raise

async def vector_search(
    mongodb: MongoClientWrapper,
    query:   str,
    limit:   int = settings.MAX_RESULTS_PER_PAGE,
    filter_criteria: Optional[Dict] = None
) -> Union[List[Tuple[Document, float]], List[Document]]:
    """
    Perform a hybrid vector and text search using the collection's hybrid retriever.

    Args:
        mongodb (MongoClientWrapper): The MongoDB client wrapper, with initialized retriever.
        query (str): The search query.
        limit (int, optional): Max number of results to return.
        filter_criteria (dict, optional): MongoDB pre_filter for vector search (if supported).

    Returns:
        Union[List[Tuple[Document, float]], List[Document]]:
            - List of (Document, score) tuples if using similarity_search_with_score.
            - List of Document if using retriever.invoke.
    """
    try:
        if not mongodb.retriever:
            raise ValueError("Hybrid search retriever not initialized. Call initialize_indexes() first.")

        retriever = mongodb.retriever
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