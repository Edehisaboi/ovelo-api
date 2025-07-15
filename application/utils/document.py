from datetime import datetime, UTC

from application.models import MovieDetails, TVDetails
from application.core.config import settings


def extract_movie_collections(movie: MovieDetails) -> dict:
    """
    Normalize a MovieDetails instance into dicts for each target collection.
    Returns:
        {
            "movie": movie_doc,
            "movie_chunks": [...],
            "movie_watch_providers": provider_doc or None
        }
    """
    movie_doc = movie.model_dump(
        exclude={
            'db_id',
            'transcript_chunks',
            'watch_providers'
        }
    )

    # Add metadata
    movie_doc["media_type"] = "movie"
    movie_doc["created_at"] = datetime.now(UTC)
    movie_doc["updated_at"] = datetime.now(UTC)
    movie_doc["embedding_model"] = settings.OPENAI_EMBEDDING_MODEL

    # Movie transcript chunks
    movie_chunks = []
    if movie.transcript_chunks:
        for chunk in movie.transcript_chunks:
            movie_chunks.append({
                "movie_id":  None,  # Fill after insert
                "index":     chunk.index,
                "text":      chunk.text,
                "embedding": chunk.embedding
            })

    # Watch providers (can be None if not present)
    movie_watch_providers = None
    # This will convert each CountryWatchProviders to dict:
    mwp_dumped = {
        country: provider.model_dump()
        for country, provider in movie.watch_providers.results.items()
    }

    if movie.watch_providers:
        movie_watch_providers = {
            "movie_id": None,  # Fill after insert
            "results":  mwp_dumped
        }

    return {
        settings.MOVIES_COLLECTION:                 movie_doc,
        settings.MOVIE_CHUNKS_COLLECTION:           movie_chunks,
        settings.MOVIE_WATCH_PROVIDERS_COLLECTION:  movie_watch_providers
    }


def extract_tv_collections(tv: TVDetails) -> dict:
    """
    Normalize a TVDetails instance into dicts for each target collection.
    Returns:
        {
            "tv_show": tv_show_doc,
            "seasons": [...],
            "episodes": [...],
            "episode_chunks": [...],
            "tv_watch_providers": provider_doc or None
        }
    """
    tv_show_doc = tv.model_dump(
        exclude={
            'db_id',
            'seasons',
            'watch_providers'
        }
    )

    # Add metadata
    tv_show_doc["media_type"] = "tv"
    tv_show_doc["created_at"] = datetime.now(UTC)
    tv_show_doc["updated_at"] = datetime.now(UTC)
    tv_show_doc["embedding_model"] = settings.OPENAI_EMBEDDING_MODEL

    seasons, episodes, episode_chunks = [], [], []

    for season in tv.seasons:
        season_doc = {
            "tv_show_id":    None,  # Fill after TV show insert
            "name":          season.name,
            "overview":      season.overview,
            "season_number": season.season_number,
            "episode_count": season.episode_count or len(season.episodes)
        }
        seasons.append(season_doc)

        for ep in season.episodes:
            episode_doc = {
                "tv_show_id":       None,    # Fill after TV show insert
                "season_id":        None,     # Fill after season insert
                "name":             ep.name,
                "overview":         ep.overview,
                "season_number":    ep.season_number,
                "episode_number":   ep.episode_number,
                "episode_type":     getattr(ep, "episode_type", None),
                "runtime":          ep.runtime
            }
            episodes.append(episode_doc)

            if ep.transcript_chunks:
                for chunk in ep.transcript_chunks:
                    episode_chunks.append({
                        "episode_id":       None,  # Fill after episode insert
                        "season_number":    ep.season_number,  # For linking to episode
                        "episode_number":   ep.episode_number,  # For linking to episode
                        "index":            chunk.index,
                        "text":             chunk.text,
                        "embedding":        chunk.embedding
                    })

    # Watch providers (can be None if not present)
    tv_watch_providers = None
    # This will convert each CountryWatchProviders to dict:
    tvwp_dumped = {
        country: provider.model_dump()
        for country, provider in tv.watch_providers.results.items()
    }
    if tv.watch_providers:
        tv_watch_providers = {
            "tv_show_id":   None,  # Fill after insert
            "results":      tvwp_dumped
        }

    return {
        settings.TV_COLLECTION:                 tv_show_doc,
        settings.TV_SEASONS_COLLECTION:         seasons,
        settings.TV_EPISODES_COLLECTION:        episodes,
        settings.TV_CHUNKS_COLLECTION:          episode_chunks,
        settings.TV_WATCH_PROVIDERS_COLLECTION: tv_watch_providers
    }
