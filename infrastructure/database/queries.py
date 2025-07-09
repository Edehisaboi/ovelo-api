from __future__ import annotations
from typing import List, Dict, Optional

from pymongo import errors

from application.core import settings
from application.core.logging import get_logger
from infrastructure.database import MongoClientWrapper
from application.models.media import MovieDetails, TVDetails

logger = get_logger(__name__)


def search_by_title(
    movie_db:   "MongoClientWrapper",
    tv_db:      "MongoClientWrapper",
    query:      str,
    exact_match: bool = False,
    language:   Optional[str] = None,
    country:    Optional[str] = None,
    limit:      int = settings.MAX_RESULTS_PER_PAGE
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

        # Execute the aggregation synchronously
        results = list(movie_db.collection.aggregate(pipeline))

        # Separate results into movies and tv_shows
        movies:     List[MovieDetails] = []
        tv_shows:   List[TVDetails] = []

        for result in results:
            result.pop("score", None)
            result.pop("sort_order", None)
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

    except errors.PyMongoError as e:
        logger.error(f"Error searching both collections: {str(e)}")
        raise


def vector_search(
    mongodb: MongoClientWrapper,
    query: str,
    limit: int = settings.MAX_RESULTS_PER_PAGE,
    filter_criteria: Optional[Dict] = None
) -> List[Dict]:
    """
    Perform a hybrid vector ++ text search using the collection's hybrid retriever.

    Args:
        mongodb (MongoClientWrapper): The MongoDB client wrapper, with initialized retriever.
        query (str): The search query.
        limit (int, optional): Max number of results to return. Uses retriever's default if None.
        filter_criteria (dict, optional): Additional filter. Not all retrievers support this.

    Returns:
        List[Dict]: List of result documents with relevance scores (if present).
    """
    try:
        # Ensure retriever is initialized
        if not hasattr(mongodb, "retriever") or not mongodb.retriever:
            raise ValueError("Hybrid search retriever not initialized. Call initialize_indexes() first.")

        # Update top_k if limit is provided and supported
        retriever = mongodb.retriever
        if limit is not None and hasattr(retriever, "top_k"):
            retriever.top_k = limit

        # LangChain's MongoDBAtlasHybridSearchRetriever does not (as of mid-2024) natively support extra filter_criteria.
        # If filter_criteria are required and retriever supports it, pass it. Else, log and skip.
        if filter_criteria:
            logger.warning("filter_criteria not applied: current retriever does not support filter params. Skipping filters.")

        # Perform the hybrid search (invoke may be async, but often is sync. Wrap if needed.)
        # If your retriever is async, use: results = await retriever.invoke(query)
        results = retriever.invoke(query)

        # Convert results to dicts
        documents = []
        for doc in results:
            # LangChain returns Document or BaseModel objects; .dict() or .to_dict() often available
            if hasattr(doc, "dict"):
                doc_dict = doc.model_dump()
            elif hasattr(doc, "model_dump"):
                doc_dict = doc.model_dump()
            else:
                doc_dict = dict(doc)
            documents.append(doc_dict)

        return documents

    except Exception as e:
        logger.error(f"Error performing vector search: {e}")
        raise