from typing import List

from application.models import (
    MovieDetails,
    SubtitleSearchResults,
    SubtitleFile,
    TranscriptChunk,
)

from application.services.media import tmdb_service
from application.services.embeddings import embedding_service
from application.services.subtitles import subtitle_processor
from application.core.resources import opensubtitles_client
from application.core.logging import get_logger
from application.core.config import settings

logger = get_logger(__name__)


class Extractor:
    """Extractor for fetching and enriching movie metadata."""

    @staticmethod
    async def extract_movie_data(movie_id: int) -> MovieDetails:
        if not movie_id:
            raise ValueError("Movie ID must be a non-zero integer.")

        try:
            # Fetch movie metadata
            movie: MovieDetails = await tmdb_service.get_movie_details(movie_id)
            if not movie:
                raise LookupError(f"No TMDb data for movie ID {movie_id}.")

            # Find and download top subtitles
            subs_result: SubtitleSearchResults = await opensubtitles_client.search.by_tmdb(movie_id)
            best = subs_result.results[0]
            file_meta: SubtitleFile = best.attributes.files[0]
            downloaded: SubtitleFile = await opensubtitles_client.subtitles.download(file_meta)
            if not (downloaded and downloaded.subtitle_text):
                raise IOError(f"Subtitle download failed for movie ID {movie_id}.")

            # Parse into transcript chunks
            chunks: List[TranscriptChunk] = subtitle_processor.process(downloaded.subtitle_text)
            if not chunks:
                raise ValueError("No valid subtitle chunks to process.")

            # Embed from chunks
            enriched: List[TranscriptChunk] = await embedding_service.update_with_embeddings(chunks)
            if not enriched or enriched[0].embedding is None:
                raise RuntimeError("Embedding enrichment failed.")

        except Exception as exc:
            # Centralized error handling
            logger.exception(f"Failed extracting movie data for ID {movie_id}")
            raise exc from None

        # Update the model
        updated_movie = movie.model_copy(update={
            "transcript_chunks": enriched,
            "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
        })

        logger.info(f"Extracted and enriched movie ID {movie_id} successfully.")

        from pprint import pprint

        pprint(updated_movie.model_dump())

        return updated_movie