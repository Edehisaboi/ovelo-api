import asyncio
from typing import List, Optional

from application.core.logging import get_logger
from application.core.resources import opensubtitles_client
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
from application.services.media import tmdb_service
from application.services.subtitles import subtitle_processor
from application.core.config import settings

logger = get_logger(__name__)

# Global semaphore to limit concurrent OpenSubtitles API requests
# OpenSubtitles allows 5 requests per second, so we'll limit to 3 concurrent requests
OPENSUBTITLES_SEMAPHORE = None  # Will be initialized after settings are loaded

def _get_opensubtitles_semaphore() -> asyncio.Semaphore:
    """Get the OpenSubtitles semaphore, initializing it if needed."""
    global OPENSUBTITLES_SEMAPHORE
    if OPENSUBTITLES_SEMAPHORE is None:
        # Use the same value as batch size for consistency
        from application.core.config import settings
        OPENSUBTITLES_SEMAPHORE = asyncio.Semaphore(settings.TV_EXTRACTION_BATCH_SIZE)
    return OPENSUBTITLES_SEMAPHORE


class Extractor:
    """Extractor for fetching and enriching movie and TV show metadata."""

    @staticmethod
    async def extract_movie_data(movie_id: int) -> MovieDetails:
        """
        Extract and enrich movie data with transcript chunks and embeddings.

        Args:
            movie_id: The TMDb ID of the movie.

        Returns:
            MovieDetails: Enriched movie data with transcript chunks.

        Raises:
            ValueError: If movie_id is invalid.
            LookupError: If no TMDb data or subtitles are found.
            IOError: If subtitle download fails.
            RuntimeError: If embedding enrichment fails.
        """
        if not movie_id:
            raise ValueError("Movie ID must be a non-zero integer.")

        try:
            # Fetch movie metadata from TMDb
            movie_details: MovieDetails = await tmdb_service.get_movie_details(movie_id)
            if not movie_details:
                raise LookupError(f"No TMDb data found for movie ID {movie_id}.")

            # Search for subtitles using OpenSubtitles
            subtitle_search_result: SubtitleSearchResult = await opensubtitles_client.search.by_tmdb(movie_id)
            if not subtitle_search_result.attributes.files:
                raise LookupError(f"No subtitles found for movie ID {movie_id}.")

            # Download the first subtitle file
            subtitle_file: SubtitleFile = subtitle_search_result.attributes.files[0]
            async with _get_opensubtitles_semaphore():
                downloaded_subtitle: SubtitleFile = await opensubtitles_client.subtitles.download(subtitle_file)
                if not downloaded_subtitle or not downloaded_subtitle.subtitle_text:
                    raise IOError(f"Subtitle download failed for movie ID {movie_id}.")

            # Process subtitle text into transcript chunks
            transcript_chunks: List[TranscriptChunk] = subtitle_processor.process(downloaded_subtitle.subtitle_text)
            if not transcript_chunks:
                raise ValueError("No valid subtitle chunks to process.")

            # Generate embeddings for the transcript chunks
            enriched_chunks: List[TranscriptChunk] = await embedding_service.update_with_embeddings(transcript_chunks)
            if not enriched_chunks or enriched_chunks[0].embedding is None:
                raise RuntimeError("Embedding enrichment failed.")

            # Update the movie model with enriched chunks
            updated_movie = movie_details.model_copy(update={
                "transcript_chunks": enriched_chunks
            })
            logger.info(f"Extracted and enriched movie ID {movie_id} successfully.")

            return updated_movie

        except Exception as exc:
            # Centralized error handling with detailed logging
            logger.exception(f"Failed extracting movie data for ID {movie_id}")
            raise exc from None

    @staticmethod
    async def extract_tv_data(tv_id: int) -> TVDetails:
        """
        Extract and enrich TV show data with transcript chunks and embeddings for each episode.

        Args:
            tv_id: The TMDb ID of the TV show.

        Returns:
            TVDetails: Enriched TV show data with transcript chunks in episodes.

        Raises:
            ValueError: If tv_id is invalid.
            LookupError: If no TMDb data or subtitles are found.
            RuntimeError: If no episodes could be processed with subtitles.
        """
        if not tv_id:
            raise ValueError("TV ID must be a non-zero integer.")

        try:
            # Fetch TV show metadata from TMDb
            tv_details: TVDetails = await tmdb_service.get_tv_details(tv_id)
            if not tv_details:
                raise LookupError(f"No TMDb data found for TV ID {tv_id}.")

            # Search for subtitles for all episodes across all seasons
            subtitle_search_results: List[Optional[SubtitleSearchResult]] = await opensubtitles_client.search.all_parent_search(
                parent_type="TMDB",
                parent_id=tv_id,
                seasons=tv_details.seasons
            )
            if not subtitle_search_results:
                raise LookupError(f"No subtitles found for TV ID {tv_id}.")

            # Process episodes with subtitles concurrently
            enriched_seasons = await Extractor._process_tv_seasons(tv_details.seasons, subtitle_search_results)
            if not enriched_seasons:
                raise RuntimeError("No episodes could be processed with subtitles.")

            # Update the TV model with enriched seasons
            updated_tv = tv_details.model_copy(update={"seasons": enriched_seasons})
            logger.info(f"Extracted and enriched TV ID {tv_id} successfully with {len(enriched_seasons)} seasons.")

            return updated_tv

        except Exception as exc:
            # Centralized error handling with detailed logging
            logger.exception(f"Failed extracting TV data for ID {tv_id}")
            raise exc from None

    @staticmethod
    async def _process_tv_seasons(
        seasons: List[Season], subtitle_search_results: List[Optional[SubtitleSearchResult]]
    ) -> List[Season]:
        """
        Process all seasons and episodes with their corresponding subtitle results.
        Uses sequential processing with small batches to respect API rate limits.

        Args:
            seasons: List of seasons from TVDetails.
            subtitle_search_results: List of subtitle search results (one per episode).

        Returns:
            List[Season]: Enriched seasons with transcript chunks in episodes.
        """
        # Create a flat list of episode processing tasks
        episode_tasks = []

        for season in seasons:
            for episode in season.episodes:
                # Find the matching subtitle result for this episode
                matching_result = next(
                    (
                        result
                        for result in subtitle_search_results
                        if result
                        and result.attributes.feature_details
                        and result.attributes.feature_details.season_number == episode.season_number
                        and result.attributes.feature_details.episode_number == episode.episode_number
                    ),
                    None,
                )
                # Create a task to process this episode
                task = Extractor._process_episode_with_subtitles(episode, matching_result)
                episode_tasks.append((season.season_number, episode.episode_number, task))

        # Process episodes in small batches to respect rate limits
        # OpenSubtitles allows 5 requests per second, so we'll use batches of 3 to be safe
        batch_size = settings.TV_EXTRACTION_BATCH_SIZE
        episode_results = []
        
        for i in range(0, len(episode_tasks), batch_size):
            batch = episode_tasks[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(episode_tasks) + batch_size - 1)//batch_size} [{len(batch)} episodes]")
            
            # Process this batch concurrently
            batch_results = await asyncio.gather(
                *[task for _, _, task in batch],
                return_exceptions=True
            )
            episode_results.extend(batch_results)
            
            # Add a small delay between batches to ensure rate limits are respected
            if i + batch_size < len(episode_tasks):
                await asyncio.sleep(settings.TV_EXTRACTION_BATCH_DELAY)  # Configurable delay between batches

        # Build a lookup dictionary: (season_number, episode_number) -> result
        episode_tasks_keys = [
            (season.season_number, episode.episode_number)
            for season in seasons
            for episode in season.episodes
        ]
        result_lookup = dict(zip(episode_tasks_keys, episode_results))

        # Reconstruct enriched seasons with processed episodes
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

            enriched_season = season.model_copy(update={"episodes": enriched_episodes})
            enriched_seasons.append(enriched_season)

        return enriched_seasons

    @staticmethod
    async def _process_episode_with_subtitles(
        episode: Episode, subtitle_search_result: Optional[SubtitleSearchResult]
    ) -> Episode:
        """
        Process a single episode with its subtitle data.
        Uses semaphore to limit concurrent OpenSubtitles API requests.

        Args:
            episode: The episode to process.
            subtitle_search_result: Subtitle search result for this episode (maybe None).

        Returns:
            Episode: Enriched episode with transcript chunks, or original if processing fails.
        """
        if not subtitle_search_result:
            logger.debug(f"No subtitles found for S{episode.season_number}E{episode.episode_number}")
            return episode

        try:
            # Use semaphore to limit concurrent API requests
            async with _get_opensubtitles_semaphore():
                # Download the first subtitle file
                subtitle_file: SubtitleFile = subtitle_search_result.attributes.files[0]
                downloaded_subtitle: SubtitleFile = await opensubtitles_client.subtitles.download(subtitle_file)
                if not downloaded_subtitle or not downloaded_subtitle.subtitle_text:
                    logger.warning(f"Subtitle download failed for S{episode.season_number}E{episode.episode_number}")
                    return episode

                # Process subtitle text into transcript chunks
                transcript_chunks: List[TranscriptChunk] = subtitle_processor.process(downloaded_subtitle.subtitle_text)
                if not transcript_chunks:
                    logger.warning(f"No valid subtitle chunks for S{episode.season_number}E{episode.episode_number}")
                    return episode

                # Generate embeddings for the transcript chunks
                enriched_chunks: List[TranscriptChunk] = await embedding_service.update_with_embeddings(transcript_chunks)
                if not enriched_chunks or enriched_chunks[0].embedding is None:
                    logger.warning(f"Embedding generation failed for S{episode.season_number}E{episode.episode_number}")
                    return episode

                # Update episode with enriched transcript chunks
                enriched_episode = episode.model_copy(update={"transcript_chunks": enriched_chunks})
                logger.debug(f"Successfully processed S{episode.season_number}E{episode.episode_number} with {len(enriched_chunks)} chunks")
                return enriched_episode

        except Exception as e:
            logger.error(f"Error processing episode S{episode.season_number}E{episode.episode_number}: {e}")
            # Return original episode on failure
            return episode