from datetime import datetime
from typing import Dict, List, Optional

from pymongo.collection import Collection
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from config import settings, get_logger, get_movie_db, get_tv_db

logger = get_logger(__name__)

#
# def _build_base_filter(
#     genre:      Optional[str] = None,
#     language:   Optional[str] = None,
#     country:    Optional[str] = None,
#     year:       Optional[int] = None,
#     date_field: str = "release_date"
# ) -> Dict:
#     """
#     Build a base filter dictionary for MongoDB queries.
#     """
#     base_filter = {}
#     if genre:
#         base_filter["genres"] = genre
#     if language:
#         base_filter["spoken_languages.name"] = language or settings.TMDB_LANGUAGE
#     if country:
#         base_filter["origin_country"] = country or settings.TMDB_REGION
#     if year:
#         base_filter[date_field] = {
#             "$gte": datetime(year, 1, 1),
#             "$lt":  datetime(year + 1, 1, 1)
#         }
#     return base_filter
#
#
# def _get_projection_fields(asset_type: str) -> Dict:
#     """
#     Get the projection fields for movies or TV shows.
#     """
#     if asset_type == "movie":
#         return {
#             "tmdb_id": 1,
#             "adult": 1,
#             "title": 1,
#             "original_title": 1,
#             "overview": 1,
#             "poster_path": 1,
#             "backdrop_path": 1,
#             "release_date": 1,
#             "runtime": 1,
#             "genres": 1,
#             "original_language": 1,
#             "spoken_languages": 1,
#             "origin_country": 1,
#             "external_ids": 1,
#             "status": 1,
#             "tagline": 1,
#             "vote_average": 1,
#             "vote_count": 1,
#             "cast": 1,
#             "crew": 1,
#             "images": 1,
#             "videos": 1,
#             "watch_providers": 1,
#             "created_at": 1,
#             "updated_at": 1
#         }
#     elif asset_type == "tv":
#         return {
#             "tmdb_id": 1,
#             "adult": 1,
#             "name": 1,
#             "original_name": 1,
#             "overview": 1,
#             "poster_path": 1,
#             "backdrop_path": 1,
#             "first_air_date": 1,
#             "last_air_date": 1,
#             "number_of_seasons": 1,
#             "number_of_episodes": 1,
#             "genres": 1,
#             "original_language": 1,
#             "spoken_languages": 1,
#             "origin_country": 1,
#             "external_ids": 1,
#             "status": 1,
#             "tagline": 1,
#             "vote_average": 1,
#             "vote_count": 1,
#             "cast": 1,
#             "crew": 1,
#             "images": 1,
#             "videos": 1,
#             "watch_providers": 1,
#             "seasons": {
#                 "season_number": 1,
#                 "name": 1,
#                 "overview": 1,
#                 "episode_count": 1,
#                 "episodes": {
#                     "season_number": 1,
#                     "episode_number": 1,
#                     "name": 1,
#                     "overview": 1,
#                 }
#             },
#             "created_at": 1,
#             "updated_at": 1
#         }
#     return {}
#
#
# def _build_vector_search_pipeline(
#     path:           str,
#     query_vector:   List[float],
#     genre:          Optional[str] = None,
#     cast_list:      Optional[List[str]] = None,
#     language:       Optional[str] = None,
#     country:        Optional[str] = None,
#     year:           Optional[int] = None,
#     limit:          int = None,
#     project_fields: Dict = None,
#     index_name:     str = None,
#     date_field:     str = "release_date"
# ) -> List[Dict]:
#     """
#     Build a MongoDB aggregation pipeline for vector similarity search with filters.
#     """
#     base_filter = _build_base_filter(genre, language, country, year, date_field)
#     search_stage = {
#         "$vectorSearch": {
#             "index": index_name or settings.MOVIE_INDEX_NAME,
#             "path":          path,
#             "queryVector":   query_vector,
#             "numCandidates": settings.NUM_CANDIDATES,
#             "limit": limit or settings.MAX_RESULTS_PER_PAGE,
#             "filter":        base_filter
#         }
#     }
#     pipeline = [search_stage]
#     if cast_list:
#         add_cast_match_stage = {
#             "$addFields": {
#                 "matched_cast_count": {
#                     "$size": {
#                         "$filter": {
#                             "input": "$cast",
#                             "as": "actor",
#                             "cond": {"$in": ["$$actor.name", cast_list]}
#                         }
#                     }
#                 }
#             }
#         }
#         sort_stage = {"$sort": {"matched_cast_count": -1, "score": -1}}
#         pipeline.append(add_cast_match_stage)
#     else:
#         sort_stage = {"$sort": {"score": -1, settings.DEFAULT_SORT_FIELD: settings.DEFAULT_SORT_ORDER}}
#     project_stage = {
#         "$project": {
#             **(project_fields or {}),
#             "score": {"$meta": "vectorSearchScore"},
#             "matched_cast_count": 1
#         }
#     }
#     pipeline += [sort_stage, project_stage]
#     return pipeline
#
#
# def search_movie_vectors(
#     collection:     Collection,
#     query_vector:   List[float],
#     limit:          int = None,
#     genre:          Optional[str] = None,
#     cast_list:      Optional[List[str]] = None,
#     language:       Optional[str] = None,
#     country:        Optional[str] = None,
#     year:           Optional[int] = None
# ) -> List[Dict]:
#     """
#     Search for movies using vector similarity and optional filters.
#     """
#     pipeline = _build_vector_search_pipeline(
#         path=settings.MOVIE_EMBEDDING_PATH,
#         query_vector=query_vector,
#         genre=genre,
#         cast_list=cast_list,
#         language=language,
#         country=country,
#         year=year,
#         limit=limit or settings.MOVIE_SEARCH_LIMIT,
#         project_fields=_get_projection_fields("movie"),
#         index_name=settings.MOVIE_INDEX_NAME,
#         date_field="release_date"
#     )
#     return list(collection.aggregate(pipeline))
#
#
# def search_tv_vectors(
#     collection:     Collection,
#     query_vector:   List[float],
#     limit:          int = None,
#     genre:          Optional[str] = None,
#     cast_list:      Optional[List[str]] = None,
#     language:       Optional[str] = None,
#     country:        Optional[str] = None,
#     year:           Optional[int] = None
# ) -> List[Dict]:
#     """
#     Search for TV shows using vector similarity and optional filters.
#     """
#     pipeline = _build_vector_search_pipeline(
#         path=settings.TV_EMBEDDING_PATH,
#         query_vector=query_vector,
#         genre=genre,
#         cast_list=cast_list,
#         language=language,
#         country=country,
#         year=year,
#         limit=limit or settings.TV_SEARCH_LIMIT,
#         project_fields=_get_projection_fields("tv"),
#         index_name=settings.TV_INDEX_NAME,
#         date_field="first_air_date"
#     )
#     return list(collection.aggregate(pipeline))
#
#
# def _build_title_search_pipeline(
#     title:          str,
#     exact_match:    bool = False,
#     language:       Optional[str] = None,
#     country:        Optional[str] = None,
#     year:           Optional[int] = None,
#     limit:          int = None,
#     project_fields: Dict = None,
#     asset_type:     str = "movie",
#     date_field:     str = "release_date"
# ) -> List[Dict]:
#     """
#     Build a MongoDB aggregation pipeline for title-based search with filters.
#     """
#     base_filter = {}
#     if exact_match:
#         if asset_type == "movie":
#             base_filter["$or"] = [
#                 {"title": title},
#                 {"original_title": title}
#             ]
#         else:
#             base_filter["$or"] = [
#                 {"name": title},
#                 {"original_name": title}
#             ]
#     else:
#         base_filter["$text"] = {"$search": title}
#     if language:
#         base_filter["spoken_languages.name"] = language or settings.TMDB_LANGUAGE
#     if country:
#         base_filter["origin_country"] = country or settings.TMDB_REGION
#     if year:
#         base_filter[date_field] = {
#             "$gte": datetime(year, 1, 1),
#             "$lt":  datetime(year + 1, 1, 1)
#         }
#     match_stage = {"$match": base_filter}
#     if exact_match:
#         sort_stage = {"$sort": {settings.DEFAULT_SORT_FIELD: settings.DEFAULT_SORT_ORDER}}
#     else:
#         sort_stage = {"$sort": {"score": {"$meta": "textScore"}}}
#     project_stage = {
#         "$project": {
#             **(project_fields or {}),
#             "score": {"$meta": "textScore"} if not exact_match else 1
#         }
#     }
#     pipeline = [match_stage, sort_stage, project_stage]
#     if limit:
#         pipeline.append({"$limit": limit or settings.MAX_RESULTS_PER_PAGE})
#     return pipeline
#
#
# def search_movie_by_title(
#     collection:     Collection,
#     title:          str,
#     exact_match:    bool = False,
#     language:       Optional[str] = None,
#     country:        Optional[str] = None,
#     year:           Optional[int] = None,
#     limit:          int = None
# ) -> List[Dict]:
#     """
#     Search for movies by title with optional filters.
#     """
#     pipeline = _build_title_search_pipeline(
#         title=title,
#         exact_match=exact_match,
#         language=language,
#         country=country,
#         year=year,
#         limit=limit or settings.MOVIE_SEARCH_LIMIT,
#         project_fields=_get_projection_fields("movie"),
#         asset_type="movie",
#         date_field="release_date"
#     )
#     return list(collection.aggregate(pipeline))
#
#
# def search_tv_by_title(
#     collection:     Collection,
#     title:          str,
#     exact_match:    bool = False,
#     language:       Optional[str] = None,
#     country:        Optional[str] = None,
#     year:           Optional[int] = None,
#     limit:          int = None
# ) -> List[Dict]:
#     """
#     Search for TV shows by title with optional filters.
#     """
#     pipeline = _build_title_search_pipeline(
#         title=title,
#         exact_match=exact_match,
#         language=language,
#         country=country,
#         year=year,
#         limit=limit or settings.TV_SEARCH_LIMIT,
#         project_fields=_get_projection_fields("tv"),
#         asset_type="tv",
#         date_field="first_air_date"
#     )
#     return list(collection.aggregate(pipeline))


def create_movie_hybrid_retriever(
    k: int = settings.RAG_TOP_K
) -> MongoDBAtlasHybridSearchRetriever:
    """Creates and returns a hybrid search retriever for movies.

    Args:
        k (int, optional): Number of documents to retrieve. Defaults to settings.RAG_TOP_K.

    Returns:
        MongoDBAtlasHybridSearchRetriever: A configured hybrid search retriever for movies.
    """
    logger.info(f"Creating movie hybrid retriever with top_k: {k}")
    return get_movie_db().get_hybrid_search_retriever(
        text_key="title",
        embedding_key=settings.MOVIE_EMBEDDING_PATH,
        index_name=settings.MOVIE_INDEX_NAME,
        similarity_metric=settings.MOVIE_SIMILARITY,
        k=k
    )


def create_tv_hybrid_retriever(
    k: int = settings.RAG_TOP_K
) -> MongoDBAtlasHybridSearchRetriever:
    """Creates and returns a hybrid search retriever for TV shows.

    Args:
        k (int, optional): Number of documents to retrieve. Defaults to settings.RAG_TOP_K.

    Returns:
        MongoDBAtlasHybridSearchRetriever: A configured hybrid search retriever for TV shows.
    """
    logger.info(f"Creating TV hybrid retriever with top_k: {k}")
    return get_tv_db().get_hybrid_search_retriever(
        text_key="name",
        embedding_key=settings.TV_EMBEDDING_PATH,
        index_name=settings.TV_INDEX_NAME,
        similarity_metric=settings.TV_SIMILARITY,
        k=k
    )
