from __future__ import annotations
from typing import List, Dict, Optional

from pymongo import errors

from application.core import settings
from application.core.logging import get_logger
from infrastructure.database import MongoClientWrapper

logger = get_logger(__name__)

async def search_by_title(
    mongodb:    MongoClientWrapper,
    title:      str,
    exact_match: bool = False,
    language:   Optional[str] = None,
    country:    Optional[str] = None,
    limit:      int = settings.MAX_RESULTS_PER_PAGE
) -> List[Dict]:
    """Search for documents by title in the database with optional filters.

    Args:
        mongodb (MongoClientWrapper): The MongoDB client wrapper.
        title (str): The title to search for.
        exact_match (bool, optional): Whether to perform an exact match search.
            Defaults to False.
        language (Optional[str], optional): Language filter. Defaults to None.
        country (Optional[str], optional): Country filter. Defaults to None.
        limit (int, optional): Maximum number of results to return.
            Defaults to settings.MAX_RESULTS_PER_PAGE.

    Returns:
        List[Dict]: List of matching documents.
    """
    try:
        match_filter = {}
        if exact_match:
            if mongodb.collection_name == settings.MOVIES_COLLECTION:
                match_filter["$or"] = [
                    {"title": title},
                    {"original_title": title}
                ]
            else:
                match_filter["$or"] = [
                    {"name": title},
                    {"original_name": title}
                ]
        else:
            match_filter["$text"] = {"$search": title}

        if language:
            match_filter["spoken_languages.name"] = language
        if country:
            match_filter["origin_country"] = country

        match_stage = {"$match": match_filter}
        pipeline = [match_stage]

        if not exact_match:
            sort_stage = {"$sort": {"score": {"$meta": "textScore"}}}
            pipeline.append(sort_stage)

        # Create projection using field aliases if defined
        projection = {
            field_info.alias or field_name: 1
            for field_name, field_info in mongodb.model.model_fields.items()
        }
        if not exact_match:
            projection["score"] = {"$meta": "textScore"}

        project_stage = {"$project": projection}
        pipeline.append(project_stage)

        if limit:
            pipeline.append({"$limit": limit})

        return list(mongodb.collection.aggregate(pipeline))
    except errors.PyMongoError as e:
        logger.error(f"Error searching {mongodb.collection_name} by title: {str(e)}")
        raise


async def vector_search(
    mongodb: MongoClientWrapper,
    query: str,
    limit: int = None,
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
        results = retriever.ainvoke(query)

        # Convert results to dicts
        documents = []
        for doc in results:
            # LangChain returns Document or BaseModel objects; .dict() or .to_dict() often available
            if hasattr(doc, "dict"):
                doc_dict = doc.dict()
            elif hasattr(doc, "to_dict"):
                doc_dict = doc.to_dict()
            else:
                doc_dict = dict(doc)
            documents.append(doc_dict)

        return documents

    except Exception as e:
        logger.error(f"Error performing vector search: {e}")
        raise