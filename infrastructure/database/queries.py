from typing import List, Dict, Optional

from application.core import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


async def search_movie_by_title(
    collection,
    title: str,
    exact_match: bool = False,
    language: Optional[str] = None,
    country: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = settings.MAX_RESULTS_PER_PAGE
) -> List[Dict]:
    """Search for movies by title in the database."""
    try:
        base_filter = {}
        if exact_match:
            base_filter["$or"] = [
                {"title": title},
                {"original_title": title}
            ]
        else:
            base_filter["$text"] = {"$search": title}

        if language:
            base_filter["spoken_languages.name"] = language or settings.TMDB_LANGUAGE
        if country:
            base_filter["origin_country"] = country or settings.TMDB_REGION
        if year:
            base_filter["release_date"] = {"$regex": f"^{year}"}

        match_stage = {"$match": base_filter}
        if exact_match:
            pipeline = [match_stage]
        else:
            sort_stage = {"$sort": {"score": {"$meta": "textScore"}}}
            pipeline = [match_stage, sort_stage]

        # Create projection
        projection = {
            "tmdb_id": 1,
            "title": 1,
            "original_title": 1,
            "overview": 1,
            "poster_path": 1,
            "backdrop_path": 1,
            "release_date": 1,
            "runtime": 1,
            "genres": 1,
            "vote_average": 1,
            "vote_count": 1,
            "status": 1
        }
        # Add score field for text search
        if not exact_match:
            projection["score"] = {"$meta": "textScore"}

        project_stage = {"$project": projection}
        pipeline.append(project_stage)

        if limit:
            pipeline.append({"$limit": limit})

        return list(collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error searching movies by title: {str(e)}")
        return []


async def search_tv_by_title(
    collection,
    title: str,
    exact_match: bool = False,
    language: Optional[str] = None,
    country: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = settings.MAX_RESULTS_PER_PAGE
) -> List[Dict]:
    """Search for TV shows by title in the database."""
    try:
        base_filter = {}
        if exact_match:
            base_filter["$or"] = [
                {"name": title},
                {"original_name": title}
            ]
        else:
            base_filter["$text"] = {"$search": title}

        if language:
            base_filter["spoken_languages.name"] = language or settings.TMDB_LANGUAGE
        if country:
            base_filter["origin_country"] = country or settings.TMDB_REGION
        if year:
            base_filter["first_air_date"] = {"$regex": f"^{year}"}

        match_stage = {"$match": base_filter}
        if exact_match:
            pipeline = [match_stage]
        else:
            sort_stage = {"$sort": {"score": {"$meta": "textScore"}}}
            pipeline = [match_stage, sort_stage]

        # Create projection
        projection = {
            "tmdb_id": 1,
            "name": 1,
            "original_name": 1,
            "overview": 1,
            "poster_path": 1,
            "backdrop_path": 1,
            "first_air_date": 1,
            "last_air_date": 1,
            "number_of_seasons": 1,
            "number_of_episodes": 1,
            "genres": 1,
            "vote_average": 1,
            "vote_count": 1,
            "status": 1
        }
        # Add score field for text search
        if not exact_match:
            projection["score"] = {"$meta": "textScore"}

        project_stage = {"$project": projection}
        pipeline.append(project_stage)

        if limit:
            pipeline.append({"$limit": limit})

        return list(collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error searching TV shows by title: {str(e)}")
        return [] 