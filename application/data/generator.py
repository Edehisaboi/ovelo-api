import asyncio
from typing import Union, AsyncGenerator, Optional
from tqdm import tqdm

from application.models import (
    MovieDetails,
    TVDetails,
    SearchResults,
    SearchResult,
)
from application.data.extract import Extractor
from application.core.logging import get_logger

logger = get_logger(__name__)


async def generate_data(
    search_results: SearchResults,
) -> AsyncGenerator[Union[MovieDetails, TVDetails], None]:
    """
    Generate enriched movie and TV show data from search results.

    Args:
        search_results: SearchResults object containing basic search results

    Yields:
        Union[MovieDetails, TVDetails]: Enriched media data with transcript chunks
    """
    progress_bar = tqdm(
        search_results.results,
        desc="Extracting enriched media data",
        unit="item",
        bar_format=(
            "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} "
            "[{elapsed}<{remaining}, {rate_fmt}] {postfix}"
        ),
        ncols=100,
        position=0,
        leave=True,
    )

    for search_result in progress_bar:
        item_name = search_result.title or search_result.name or f"TMDB ID: {search_result.tmdb_id}"
        try:
            progress_bar.set_postfix_str(f"Processing: {item_name}")
            enriched_media = await _extract_media_details(search_result)
            if enriched_media:
                progress_bar.set_postfix_str(f"✓ {item_name}")
                yield enriched_media
            else:
                progress_bar.set_postfix_str(f"✕ {item_name} (no data)")
        except Exception as exc:
            logger.error(f"Failed to extract data for {item_name} (ID: {search_result.tmdb_id}): {exc}")
            progress_bar.set_postfix_str(f"✕ {item_name} (error)")
            continue

    progress_bar.close()
    logger.info(f"Completed processing {len(search_results.results)} search results.")


async def _extract_media_details(
    search_result: SearchResult,
) -> Optional[Union[MovieDetails, TVDetails]]:
    """
    Extract full details for a single search result.

    Args:
        search_result: Basic search result from TMDb

    Returns:
        Optional[Union[MovieDetails, TVDetails]]: Enriched media data or None if extraction fails
    """
    try:
        media_type = _determine_media_type(search_result)
        if media_type == "movie":
            return await Extractor.extract_movie_data(search_result.tmdb_id)
        elif media_type == "tv":
            return await Extractor.extract_tv_data(search_result.tmdb_id)
        else:
            logger.warning(f"Unknown media type for ID {search_result.tmdb_id}: {media_type}")
            return None
    except Exception as exc:
        logger.error(f"Error extracting details for ID {search_result.tmdb_id}: {exc}")
        return None


def _determine_media_type(search_result: SearchResult) -> Optional[str]:
    """
    Determine the media type from a search result.

    Args:
        search_result: SearchResult object from TMDb

    Returns:
        Optional[str]: Media type ('movie', 'tv', or None)
    """
    if search_result.media_type:
        return search_result.media_type.lower()
    if search_result.title is not None:
        return "movie"
    if search_result.name is not None:
        return "tv"
    if search_result.first_air_date is not None:
        return "tv"
    if search_result.release_date is not None:
        return "movie"
    return None


async def generate_data_batch(
    search_results: SearchResults,
    batch_size: int = 5,
    max_concurrent: int = 3,
) -> AsyncGenerator[Union[MovieDetails, TVDetails], None]:
    """
    Generate enriched media data with concurrent processing in batches.

    Args:
        search_results: SearchResults object containing basic search results
        batch_size: Number of items to process in each batch
        max_concurrent: Maximum number of concurrent extraction tasks

    Yields:
        Union[MovieDetails, TVDetails]: Enriched media data with transcript chunks
    """
    total_items = len(search_results.results)
    progress_bar = tqdm(
        total=total_items,
        desc="Extracting enriched media data (concurrent)",
        unit="item",
        bar_format=(
            "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} "
            "[{elapsed}<{remaining}, {rate_fmt}] {postfix}"
        ),
        ncols=100,
        position=0,
        leave=True,
    )

    for i in range(0, total_items, batch_size):
        batch = search_results.results[i : i + batch_size]
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(result: SearchResult):
            async with semaphore:
                return await _extract_media_details(result)

        tasks = [process_with_semaphore(result) for result in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, result in enumerate(results):
            item = batch[j]
            item_name = item.title or item.name or f"ID: {item.tmdb_id}"
            if isinstance(result, Exception):
                logger.error(f"Failed to extract data for {item_name}: {result}")
                progress_bar.set_postfix_str(f"✕ {item_name}")
            elif result is not None:
                progress_bar.set_postfix_str(f"✓ {item_name}")
                yield result
            else:
                progress_bar.set_postfix_str(f"✕ {item_name} (no data)")
            progress_bar.update(1)

    progress_bar.close()
    logger.info(f"Completed processing {total_items} search results with concurrent extraction.")
