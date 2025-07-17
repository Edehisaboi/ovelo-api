from typing import List, Dict, Tuple, Optional

from langchain_core.documents import Document
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from application.core.logging import get_logger
from application.models.media import MovieDetails, TVDetails

from infrastructure.database import MongoCollectionsManager

logger = get_logger(__name__)


async def search_by_title(
    manager:  MongoCollectionsManager,
    query:    str,
    limit:    int = settings.MAX_RESULTS_PER_PAGE
) -> tuple[List[MovieDetails], List[TVDetails]]:
    """
    Text search for both movies and TV shows using $text and $unionWith.

    Args:
        manager (MongoCollectionsManager): The database collections manager.
        query (str): The text search query.
        limit (int): Max results to return.

    Returns:
        List[Dict]: List of combined search results.
    """
    try:
        pipeline = [
            {
                '$match': {
                    '$text': {
                        '$search': query
                    }
                }
            },
            {
                '$addFields': {
                    'newField': {
                        'score': {
                            '$meta': 'textScore'
                        },
                        'media_type': 'movie'
                    }
                }
            },
            {
                '$unionWith': {
                    'coll': manager.tv_shows.collection_name,
                    'pipeline': [
                        {
                            '$match': {
                                '$text': {
                                    '$search': query
                                }
                            }
                        },
                        {
                            '$addFields': {
                                'score': {
                                    '$meta': 'textScore'
                                },
                                'media_type': 'tv'
                            }
                        }
                    ]
                }
            },
            {
                '$sort': {
                    'score': {
                        '$meta': 'textScore'
                    }
                }
            },
            {
                '$limit': limit
            }
        ]

        movie, tv = [], []
        # Execute aggregation
        async for doc in manager.movies.collection.aggregate(pipeline):
            if doc.get('media_type') == 'movie':
                movie.append(MovieDetails.model_validate(doc))

            elif doc.get('media_type') == 'tv':
                tv.append(TVDetails.model_validate(doc))

            else:
                logger.warning(f"Unexpected media type in search results: {doc.get('media_type')}")

        return movie, tv

    except Exception as e:
        logger.error(f"Error in search_by_title: {str(e)}")
        raise


async def vector_search(
    retriever:  MongoDBAtlasHybridSearchRetriever,
    query:      str,
    limit:      int = settings.MAX_RESULTS_PER_PAGE,
    filter_criteria: Optional[Dict] = None
) -> Optional[List[Tuple[Document, float]]]:
    try:
        if not retriever:
            raise ValueError(
                "Vector search retriever not initialized for this collection."
            )
        vector_store = retriever.vectorstore

        if vector_store:
            # Returns List[Tuple[Document, float]]
            documents = await vector_store.asimilarity_search_with_score(
                query=query,
                k=limit,
                pre_filter=filter_criteria
            )
            return documents
        return None

    except Exception as e:
        logger.error(f"Error performing vector search: {e}")
        raise

async def hybrid_search(
    retriever:  MongoDBAtlasHybridSearchRetriever,
    query:      str,
    limit:      int = settings.MAX_RESULTS_PER_PAGE,
    filter_criteria: Optional[Dict] = None
) -> List[Document]:
    try:
        if not retriever:
            raise ValueError(
                "Hybrid-vector search retriever not initialized for this collection."
            )

        # Returns List[Document]
        documents: List[Document] = await retriever.ainvoke(
            input=query,
            k=limit,
            pre_filter=filter_criteria
        )
        return documents

    except Exception as e:
        logger.error(f"Error performing hybrid-vector search: {e}")
        raise
