from typing import List, Dict

from application.core.config import settings
from application.core.logging import get_logger
from application.models.media import MovieDetails, TVDetails

from infrastructure.database import MongoCollectionsManager

logger = get_logger(__name__)


async def search_by_title(
    manager: MongoCollectionsManager,
    query: str,
    limit: int = settings.MAX_RESULTS_PER_PAGE
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


#
# async def vector_search(
#     wrapper:    CollectionWrapper,
#     query:      str,
#     limit:      int = settings.MAX_RESULTS_PER_PAGE,
#     filter_criteria: Optional[Dict] = None
# ) -> Union[List[Tuple[Document, float]], List[Document]]:
#     """
#     Perform a hybrid vector and text search using the collection's hybrid retriever.
#
#     Args:
#         wrapper (CollectionWrapper): Collection wrapper with an initialized retriever.
#         query (str): The search query.
#         limit (int, optional): Max number of results to return.
#         filter_criteria (dict, optional): MongoDB pre_filter for vector search (if supported).
#
#     Returns:
#         Union[List[Tuple[Document, float]], List[Document]]:
#             - List of (Document, score) tuples if using similarity_search_with_score.
#             - List of Document if using retriever.invoke.
#     """
#     try:
#         # TODO: Check if the collection has a hybrid retriever initialized, IT DOES NOT CHECK IF THE COLLECTION IS A VECTOR STORE
#         retriever = getattr(wrapper, "retriever", None)
#         if not retriever:
#             raise ValueError(
#                 "Hybrid search retriever not initialized for this collection."
#             )
#         vectorstore = retriever.vectorstore
#
#         if vectorstore:
#             # Returns List[Tuple[Document, float]]
#             documents = await vectorstore.asimilarity_search_with_score(
#                 query=query,
#                 k=limit,
#                 pre_filter=filter_criteria
#             )
#         else:
#             # Returns List[Document]
#             documents = await retriever.ainvoke(query)
#
#         return documents
#
#     except Exception as e:
#         logger.error(f"Error performing vector search: {e}")
#         raise
