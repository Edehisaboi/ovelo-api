from bson import ObjectId
from bson.errors import InvalidId
from typing import List, Literal, Dict, Tuple, Optional, Any, Sequence, Mapping

from pymongo.collation import Collation

from langchain_core.documents import Document
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from application.core.logging import get_logger
from application.models.media import SearchResult

from infrastructure.database import MongoCollectionsManager

logger = get_logger(__name__)


async def search_by_title(
    manager:  MongoCollectionsManager,
    query:    str,
    limit:    int = settings.MAX_RESULTS_PER_PAGE
) -> List[SearchResult]:
    """
    Text search for both movies and TV shows using $text and $unionWith.

    Args:
        manager (MongoCollectionsManager): The database collections manager.
        query (str): The text search query.
        limit (int): Max results to return.

    Returns:
        List[SearchResult]: List of combined search results.
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
                        }
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
                                }
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
                '$unset': _AVOID_THESE_FIELDS
            },
            {
                '$limit': limit
            }
        ]

        results: SearchResult = []
        # Execute aggregation
        async for doc in manager.movies.collection.aggregate(pipeline):
            try:
                search_result = SearchResult(
                    id=doc.get('tmdb_id'),
                    title=doc.get('title'),
                    name=doc.get('name'),
                    overview=doc.get('overview'),
                    poster_path=doc.get('poster_path'),
                    backdrop_path=doc.get('backdrop_path'),
                    media_type=doc.get('media_type'),
                    release_date=doc.get('release_date'),
                    first_air_date=doc.get('first_air_date'),
                    vote_average=doc.get('vote_average'),
                    vote_count=doc.get('vote_count'),
                    original_language=doc.get('original_language'),
                    genres=_format_genres_into_str(doc.get('genres', [])),
                    trailer_link=_find_trailer_link(doc.get('videos', {})),
                )
                results.append(search_result)
            except Exception as e:
                logger.warning(f"Failed to convert document to SearchResult: {e}")
                logger.debug(f"Document that failed: {doc}")
                continue

        return results

    except Exception as e:
        logger.error(f"Error in search_by_title: {str(e)}")
        raise

async def matched_actors(
    mongo_db: MongoCollectionsManager,
    ids:      List[str],
    actors:   List[str],
    media:    Literal["movie", "tv"],
) -> Dict[str, List[str]]:
    """
    Return { id: [matched_actor_names...] } where names are lowercased and ordered
    as in the input 'actors' list.
    """
    if not ids:
        return {}

    # Select collection
    if media == "movie":
        coll = mongo_db.movies.collection
    elif media == "tv":
        coll = mongo_db.tv_shows.collection
    else:
        raise ValueError("media must be 'movie' or 'tv'")

    # Parse ObjectIds; keep a map back to original strings
    oids: List[ObjectId] = []
    id_map: Dict[str, str] = {}
    for s in ids:
        try:
            oid = ObjectId(s)
            oids.append(oid)
            id_map[str(oid)] = s
        except InvalidId:
            pass

    # Default output: empty matches for all requested ids
    out: Dict[str, List[str]] = {s: [] for s in ids}

    if not oids:
        return out

    try:
        pipeline = [
            {"$match": {"_id": {"$in": oids}}},
            {
                "$project": {
                    "matched": {
                        "$let": {
                            "vars": {
                                # Lowercased cast list from DB: credits.cast[].name
                                "cast_lower": {
                                    "$setUnion": [
                                        [],
                                        {
                                            "$map": {
                                                "input": {"$ifNull": ["$credits.cast", []]},
                                                "as": "c",
                                                "in": {
                                                    "$toLower": {
                                                        "$trim": {"input": {"$ifNull": ["$$c.name", ""]}}
                                                    }
                                                },
                                            }
                                        },
                                    ]
                                },
                                # Normalised query actors (lowercase+trim), keep order
                                "query_norm": {
                                    "$map": {
                                        "input": actors,
                                        "as": "q",
                                        "in": {
                                            "$toLower": {
                                                "$trim": {"input": {"$ifNull": ["$$q", ""]}}
                                            }
                                        },
                                    }
                                },
                            },
                            "in": {
                                # Preserve the order of query_norm; include only those present in cast_lower
                                "$filter": {
                                    "input": "$$query_norm",
                                    "as": "q",
                                    "cond": {"$in": ["$$q", "$$cast_lower"]},
                                }
                            },
                        }
                    }
                }
            },
            {"$replaceRoot": {"newRoot": {"id": "$_id", "matched": "$matched"}}},
        ]

        # Collation isn't strictly required since we normalise to lowercase,
        # but it's harmless; keep consistent with your other pipeline.
        collation = Collation(locale="en", strength=1, normalization=True)
        cur = coll.aggregate(pipeline, collation=collation)
        rows = await cur.to_list(length=None)

        for r in rows:
            oid_str = str(r["id"])
            key = id_map.get(oid_str, oid_str)
            # r["matched"] is already a list of lowercased, trimmed names
            out[key] = [a for a in r.get("matched", []) if a]

        return out

    except Exception as e:
        logger.error(f"Error computing matched actors: {e}")
        raise


async def fetch_media_summary(
    mongo_db:   MongoCollectionsManager,
    media_type: str,
    media_id:   str
) -> Dict[str, Any]:
    try:
        object_id = ObjectId(media_id)
    except InvalidId:
        return {}

    if media_type == "movie":
        coll = mongo_db.movies.collection
    elif media_type == "tv":
        coll = mongo_db.tv_shows.collection
    else:
        raise ValueError("media must be 'movie' or 'tv'")

    pipeline = [
        {
            '$match': {
                '_id': object_id,
            }
        }, {
            '$unset': _AVOID_THESE_FIELDS
        }, {
            '$limit': 1
        }
    ]

    cursor = coll.aggregate(pipeline)
    doc = await anext(cursor, None)
    if doc and "genres" in doc:
        doc["genres"] = _format_genres_into_str(doc.get("genres", []))
        doc["trailerUrl"] = _find_trailer_link(doc.get("videos", {}))
    return doc or {}


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


def _format_genres_into_str(genres: Any) -> Optional[str]:
    return " | ".join(g["name"] for g in genres if "name" in g)

def _find_trailer_link(videos: Any) -> Optional[str]:
    if not videos:
        return None

    results: Sequence[Mapping[str, Any]] = (
        videos.get("results", []) if isinstance(videos, dict) else videos
    )
    if not results:
        return None

    # Only trailers (ignore teasers/featurettes)
    trailers = [v for v in results if str(v.get("type", "")).lower() == "trailer"]
    if not trailers:
        return None

    def _url(v: Mapping[str, Any]) -> Optional[str]:
        key = v.get("key")
        site = str(v.get("site", "")).lower()
        if not key:
            return None
        if site == "youtube":
            return f"{settings.YOUTUBE_BASE_URL}{key}"
        return None  # unknown site

    # Sort so preferred item comes first:
    # 1) official True first
    # 2) YouTube before others
    # 3) higher "size" (resolution) first
    # 4) English before others (light tie-breaker)
    def _sort_key(v: Mapping[str, Any]):
        return (
            0 if v.get("official") else 1,
            0 if str(v.get("site", "")).lower() == "youtube" else 1,
            -(v.get("size") or 0),
            0 if v.get("iso_639_1") in (None, "en") else 1,
        )

    for v in sorted(trailers, key=_sort_key):
        u = _url(v)
        if u:
            return u
    return None

_AVOID_THESE_FIELDS = [
    '_id', 'images', 'credits', 'external_ids', 'embedding', 'embedding_model',
    'origin_country', 'spoken_languages', 'updated_at', 'created_at'
]