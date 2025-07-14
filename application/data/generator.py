import asyncio
from typing import Union, AsyncGenerator, Optional

from tqdm import tqdm

from application.core.config import settings
from application.models import (
    MovieDetails,
    TVDetails,
    SearchResults,
    SearchResult,
)
from application.data.extract import Extractor
from application.core.logging import get_logger
from application.core.resources import mongo_manager

from infrastructure.database.mongodb import MongoCollectionsManager

logger = get_logger(__name__)


def _determine_media_type(
    search_result: SearchResult
) -> Optional[str]:
    """
    Determine the media type from a search result.
    Returns 'movie', 'tv', or None.
    """
    if search_result.media_type:
        return search_result.media_type.lower()
    if search_result.title is not None:
        return "movie"
    if search_result.name is not None or search_result.first_air_date is not None:
        return "tv"
    if search_result.release_date is not None:
        return "movie"
    return None


async def _should_skip_media(
    manager: MongoCollectionsManager,
    search_result: SearchResult,
) -> bool:
    """
    Determines if a media item should be skipped during processing.

    Returns True if:
      - The item already exists in the database, OR
      - The item does NOT exist, but its original_language is not allowed.

    Returns False only if:
      - The item does not exist AND its language is allowed (should be processed).
    """
    media_type = _determine_media_type(search_result)
    tmdb_id = str(search_result.tmdb_id)

    exists = False
    if media_type == "movie":
        exists = await manager.model_exists(tmdb_id, settings.MOVIES_COLLECTION)
    elif media_type == "tv":
        exists = await manager.model_exists(tmdb_id, settings.TV_COLLECTION)

    if exists:
        return True

    # Not in database; check language
    if search_result.original_language != settings.TMDB_ALLOWED_LANGUAGE:
        return True  # Not allowed, skip

    return False  # Does not exist, and language allowed; process it


async def _extract_media_details(
    search_result: SearchResult
) -> Optional[Union[MovieDetails, TVDetails]]:
    """
    Extract full details for a single search result.
    """
    media_type = _determine_media_type(search_result)
    try:
        if media_type == "movie":
            return await Extractor.extract_movie_data(search_result.tmdb_id)
        elif media_type == "tv":
            return await Extractor.extract_tv_data(search_result.tmdb_id)
        else:
            logger.warning(f"Unknown media type for ID {search_result.tmdb_id}: {media_type}")
    except Exception as exc:
        logger.error(f"Error extracting details for ID {search_result.tmdb_id}: {exc}")
    return None


async def _process_search_result(
    manager: MongoCollectionsManager,
    search_result: SearchResult,
) -> Optional[Union[MovieDetails, TVDetails]]:
    """
    Process a single search result: check existence, extract details if needed.
    Uses the provided mongo manager.
    """
    item_name = search_result.title or search_result.name or f"TMDB ID: {search_result.tmdb_id}"
    if await _should_skip_media(manager, search_result):
        logger.info(f"Skipping existing item: {item_name} ID: {search_result.tmdb_id}")
        return None
    try:
        return await _extract_media_details(search_result)
    except Exception as exc:
        logger.error(f"Failed to extract data for {item_name} ID: {search_result.tmdb_id}: {exc}")
        return None


async def generate_data(
    search_results: SearchResults,
    max_items: Optional[int] = settings.MAX_INGESTION_ITEMS,
    manager: Optional[MongoCollectionsManager] = None,
) -> AsyncGenerator[Union[MovieDetails, TVDetails], None]:
    """
    Generate enriched movie and TV show data from search results sequentially.

    Args:
        search_results (SearchResults): Object containing basic search results
        max_items (Optional[int]): Limit number of items processed
        manager: Optional MongoDB manager instance to use (creates new one if not provided)

    Yields:
        Union[MovieDetails, TVDetails]: Enriched media data with transcript chunks
    """
    results = search_results.results[:max_items] if max_items is not None else search_results.results
    total_items = len(results)
    progress_bar = tqdm(
        results,
        desc="Extracting enriched media data",
        unit="item",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}",
        ncols=100,
        position=0,
        leave=True,
    )

    # Use provided manager or create new one
    if manager is None:
        manager = await mongo_manager()

    for search_result in progress_bar:
        item_name = search_result.title or search_result.name or f"TMDB ID: {search_result.tmdb_id}"
        try:
            progress_bar.set_postfix_str(f"Processing: {item_name}")
            enriched_media = await _process_search_result(manager, search_result)
            if enriched_media:
                progress_bar.set_postfix_str(f"✓ {item_name}")
                yield enriched_media
            else:
                progress_bar.set_postfix_str(f"Skipped/Failed: {item_name}")
        except Exception as exc:
            logger.error(f"Unexpected error for {item_name} ID: {search_result.tmdb_id}: {exc}")
            progress_bar.set_postfix_str(f"✕ {item_name} (error)")

    progress_bar.close()
    logger.info(f"Completed processing {total_items} search results.")


async def generate_data_batch(
    search_results: SearchResults,
    batch_size: int = settings.TV_EXTRACTION_BATCH_SIZE,
    max_items: Optional[int] = None,
    manager: Optional[MongoCollectionsManager] = None,
) -> AsyncGenerator[Union[MovieDetails, TVDetails], None]:
    """
    Generate enriched media data with concurrent processing in batches.

    Args:
        search_results (SearchResults): Object containin    g basic search results
        batch_size (int): Number of items to process in each batch
        max_items (Optional[int]): Limit number of items processed
        manager: Optional MongoDB manager instance to use (creates new one if not provided)

    Yields:
        Union[MovieDetails, TVDetails]: Enriched media data with transcript chunks
    """
    results_to_process = search_results.results[:max_items] if max_items is not None else search_results.results
    total_items = len(results_to_process)
    progress_bar = tqdm(
        total=total_items,
        desc="Extracting enriched media data (concurrent)",
        unit="item",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}",
        ncols=100,
        position=0,
        leave=True,
    )

    # Use provided manager or create new one
    if manager is None:
        manager = await mongo_manager()

    # Semaphore to limit max concurrency (across all batches)
    semaphore = asyncio.Semaphore(batch_size)

    async def process_with_semaphore(result: SearchResult) -> Optional[Union[MovieDetails, TVDetails]]:
        async with semaphore:
            return await _process_search_result(manager, result)

    for i in range(0, total_items, batch_size):
        batch = results_to_process[i : i + batch_size]
        tasks = [process_with_semaphore(result) for result in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, result in enumerate(batch_results):
            item = batch[j]
            item_name = item.title or item.name or f"TMDB ID: {item.tmdb_id}"
            if isinstance(result, Exception):
                logger.error(f"Failed to extract data for {item_name} ID: {item.tmdb_id}: {result}")
                progress_bar.set_postfix_str(f"✕ {item_name} (error)")
            elif result is not None:
                progress_bar.set_postfix_str(f"✓ {item_name}")
                yield result
            else:
                progress_bar.set_postfix_str(f"Skipped/Failed: {item_name}")
            progress_bar.update(1)

    progress_bar.close()
    logger.info(f"Completed processing {total_items} search results with concurrent extraction.")
