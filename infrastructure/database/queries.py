from bson import ObjectId
from bson.errors import InvalidId
from typing import List, Literal, Dict, Tuple, Optional

from pymongo.collation import Collation

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


async def has_actors(
    manager: MongoCollectionsManager,
    id: str,
    actors: List[str],
    media: Literal['movie', 'tv']
) -> dict[str, bool | list[str]]:
    """Return whether all specified actors exist for this title and which are missing."""
    if media == "movie":
        coll = manager.movies.collection
    elif media == "tv":
        coll = manager.tv_shows.collection
    else:
        raise ValueError("media must be 'movie' or 'tv'")

    try:
        oid = ObjectId(id)
    except InvalidId:
        # bad id -> treat as not found
        return {"exists": False, "missing": list(actors)}

    try:
        pipeline = [
            {
                '$match': {
                    '_id': oid
                }
            }, {
                '$project': {
                    'result': {
                        '$let': {
                            'vars': {
                                'cast': {
                                    '$setUnion': [
                                        [], {
                                            '$map': {
                                                'input': {
                                                    '$ifNull': [
                                                        '$credits.cast', []
                                                    ]
                                                },
                                                'as': 'c',
                                                'in': {
                                                    '$trim': {
                                                        'input': '$$c.name'
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                },
                                'query': {
                                    '$setUnion': [
                                        [],
                                        actors
                                    ]
                                }
                            },
                            'in': {
                                'missing': {
                                    '$setDifference': [
                                        '$$query', '$$cast'
                                    ]
                                },
                                'exists': {
                                    '$eq': [
                                        {
                                            '$size': {
                                                '$setDifference': [
                                                    '$$query', '$$cast'
                                                ]
                                            }
                                        }, 0
                                    ]
                                }
                            }
                        }
                    }
                }
            }, {
                '$replaceRoot': {
                    'newRoot': '$result'
                }
            }
        ]

        collation = Collation(locale="en", strength=1, normalization=True)
        cursor = coll.aggregate(pipeline, collation=collation)
        result = await cursor.to_list(length=1)
        if not result:
            return {"exists": False, "missing": actors}
        return result[0]

    except Exception as e:
        logger.error(f"Error checking actors in database: {str(e)}")
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
