import asyncio
from typing import List, Optional

from application.core.logging import get_logger
from application.core.dependencies import opensubtitles_client
from application.models import (
    Episode,
    MovieDetails,
    Season,
    SubtitleFile,
    SubtitleSearchResult,
    TranscriptChunk,
    TVDetails
)
from application.services.embeddings import embedding_service
from application.services.media.tmdb import tmdb_service
from application.services.subtitles.processor import subtitle_processor
from application.core.config import settings

logger = get_logger(__name__)


_OPENSUBTITLES_SEMAPHORE: Optional[asyncio.Semaphore] = None

def get_opensubtitles_download_semaphore() -> asyncio.Semaphore:
    """Get or create the semaphore for OpenSubtitles API rate limiting."""
    global _OPENSUBTITLES_SEMAPHORE
    if _OPENSUBTITLES_SEMAPHORE is None:
        _OPENSUBTITLES_SEMAPHORE = asyncio.Semaphore(settings.TV_EXTRACTION_BATCH_SIZE)
    return _OPENSUBTITLES_SEMAPHORE


class Extractor:
    """Extractor for fetching and enriching movie and TV show metadata."""

    @staticmethod
    async def extract_movie_data(movie_id: int) -> MovieDetails:
        """Extract and enrich movie data with transcript chunks and embeddings."""
        if not movie_id:
            raise ValueError("Movie ID must be a non-zero integer.")

        try:
            movie_details: MovieDetails = await tmdb_service.get_movie_details(movie_id)
            if not movie_details:
                raise LookupError(f"No TMDb data found for movie ID {movie_id}.")

            subtitle_search_result: SubtitleSearchResult = await opensubtitles_client().search.by_tmdb(movie_id)
            if not subtitle_search_result.attributes.files:
                raise LookupError(f"No subtitles found for movie ID {movie_id}.")

            subtitle_file: SubtitleFile = subtitle_search_result.attributes.files[0]
            async with get_opensubtitles_download_semaphore():
                downloaded_subtitle: SubtitleFile = await opensubtitles_client().subtitles.download(subtitle_file)
                if not downloaded_subtitle or not downloaded_subtitle.subtitle_text:
                    raise IOError(f"Subtitle download failed for movie ID {movie_id}.")

            transcript_chunks: List[TranscriptChunk] = subtitle_processor.process(downloaded_subtitle.subtitle_text)
            if not transcript_chunks:
                raise ValueError("No valid subtitle chunks to process.")

            enriched_chunks: List[TranscriptChunk] = await embedding_service.update_with_embeddings(transcript_chunks)
            if not enriched_chunks or enriched_chunks[0].embedding is None:
                raise RuntimeError("Embedding enrichment failed.")

            updated_movie = movie_details.model_copy(update={
                "transcript_chunks": enriched_chunks
            })
            logger.info(f"Extracted and enriched movie ID {movie_id} successfully.")

            return updated_movie

        except Exception as exc:
            logger.exception(f"Failed extracting movie data for ID {movie_id}")
            raise exc from None

    @staticmethod
    async def extract_tv_data(tv_id: int) -> TVDetails:
        """Extract and enrich TV show data with transcript chunks and embeddings for each episode."""
        if not tv_id:
            raise ValueError("TV ID must be a non-zero integer.")

        try:
            tv_details: TVDetails = await tmdb_service.get_tv_details(tv_id)
            if not tv_details:
                raise LookupError(f"No TMDb data found for TV ID {tv_id}.")

            subtitle_search_results: List[Optional[SubtitleSearchResult]] = await opensubtitles_client().search.all_parent_search(
                parent_type="TMDB",
                parent_id=tv_id,
                seasons=tv_details.seasons
            )
            if not subtitle_search_results:
                raise LookupError(f"No subtitles found for TV ID {tv_id}.")

            enriched_seasons = await Extractor._process_tv_seasons(tv_details.seasons, subtitle_search_results)
            if not enriched_seasons:
                raise RuntimeError("No episodes could be processed with subtitles.")

            updated_tv = tv_details.model_copy(update={"seasons": enriched_seasons})
            logger.info(f"Extracted and enriched TV ID {tv_id} successfully with {len(enriched_seasons)} seasons.")
            return updated_tv

        except Exception as exc:
            logger.exception(f"Failed extracting TV data for ID {tv_id}")
            raise exc from None

    @staticmethod
    async def _process_tv_seasons(
        seasons: List[Season],
        subtitle_search_results: List[Optional[SubtitleSearchResult]],
    ) -> List[Season]:
        """
        Process all seasons and episodes with their corresponding subtitle results.
        Uses batching and concurrency to respect API rate limits.
        """
        episode_tasks = []
        for season in seasons:
            for episode in season.episodes:
                matching_result = next(
                    (
                        result for result in subtitle_search_results
                        if result
                        and result.attributes.feature_details
                        and result.attributes.feature_details.season_number == episode.season_number
                        and result.attributes.feature_details.episode_number == episode.episode_number
                    ),
                    None,
                )
                task = Extractor._process_episode_with_subtitles(episode, matching_result)
                episode_tasks.append((season.season_number, episode.episode_number, task))

        batch_size = settings.TV_EXTRACTION_BATCH_SIZE
        episode_results = []

        # Batched processing for rate limits
        for i in range(0, len(episode_tasks), batch_size):
            batch = episode_tasks[i:i + batch_size]
            logger.info(
                f"Processing batch {i//batch_size + 1}/{(len(episode_tasks) + batch_size - 1)//batch_size} "
                f"[{len(batch)} episodes]"
            )
            batch_results = await asyncio.gather(
                *[task for _, _, task in batch],
                return_exceptions=True
            )
            episode_results.extend(batch_results)
            if i + batch_size < len(episode_tasks):
                await asyncio.sleep(settings.TV_EXTRACTION_BATCH_DELAY)

        # Lookup and reconstruction
        episode_tasks_keys = [
            (season.season_number, episode.episode_number)
            for season in seasons
            for episode in season.episodes
        ]
        result_lookup = dict(zip(episode_tasks_keys, episode_results))

        enriched_seasons = []
        for season in seasons:
            enriched_episodes = []
            for episode in season.episodes:
                result = result_lookup.get((season.season_number, episode.episode_number))
                if isinstance(result, Exception):
                    logger.warning(f"Failed to process S{season.season_number}E{episode.episode_number}: {result}")
                    enriched_episodes.append(episode)
                elif result is not None:
                    enriched_episodes.append(result)
                else:
                    logger.warning(f"No subtitles found for S{season.season_number}E{episode.episode_number}")
                    enriched_episodes.append(episode)
            enriched_seasons.append(season.model_copy(update={"episodes": enriched_episodes}))
        return enriched_seasons

    @staticmethod
    async def _process_episode_with_subtitles(
        episode: Episode,
        subtitle_search_result: Optional[SubtitleSearchResult],
    ) -> Episode:
        """
        Process a single episode with its subtitle data, rate-limited.
        Returns episode with transcript chunks if successful, otherwise original episode.
        """
        if not subtitle_search_result:
            logger.debug(f"No subtitles found for S{episode.season_number}E{episode.episode_number}")
            return episode

        try:
            async with get_opensubtitles_download_semaphore():
                subtitle_file: SubtitleFile = subtitle_search_result.attributes.files[0]
                downloaded_subtitle: SubtitleFile = await opensubtitles_client().subtitles.download(subtitle_file)
                if not downloaded_subtitle or not downloaded_subtitle.subtitle_text:
                    logger.warning(f"Subtitle download failed for S{episode.season_number}E{episode.episode_number}")
                    return episode

            transcript_chunks: List[TranscriptChunk] = subtitle_processor.process(downloaded_subtitle.subtitle_text)
            if not transcript_chunks:
                logger.warning(f"No valid subtitle chunks for S{episode.season_number}E{episode.episode_number}")
                return episode

            enriched_chunks: List[TranscriptChunk] = await embedding_service.update_with_embeddings(transcript_chunks)
            if not enriched_chunks or enriched_chunks[0].embedding is None:
                logger.warning(f"Embedding generation failed for S{episode.season_number}E{episode.episode_number}")
                return episode

            return episode.model_copy(
                update={
                    "transcript_chunks": enriched_chunks
                }
            )

        except Exception as e:
            logger.error(f"Error processing episode S{episode.season_number}E{episode.episode_number}: {e}")
            return episode
