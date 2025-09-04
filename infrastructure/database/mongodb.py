import asyncio
from typing import List, TypeVar, Optional, Dict, Type

from typing_extensions import Self
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

from application.core.config import settings
from application.core.logging import get_logger
from application.models.media import MovieDetails, TVDetails
from application.utils.document import extract_movie_collections, extract_tv_collections

from external.clients import EmbeddingClient
from infrastructure.database.collection import CollectionWrapper
from infrastructure.database.indexes import MongoIndex

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class MongoCollectionsManager:
    """
    Central manager for all MongoDB collections with property-based API, including vector retrievers.
    Use as an async context manager.
    """

    def __init__(
        self,
        mongodb_uri:        str,
        database_name:      str,
        embedding_client:   Optional[EmbeddingClient] = None
    ):
        self.database_name    = database_name
        self.mongodb_uri      = mongodb_uri
        self.embedding_client = embedding_client

        self.client                 : Optional[AsyncIOMotorClient] = None
        self.database               : Optional[AsyncIOMotorDatabase] = None
        self._collection_wrappers   : Dict[str, CollectionWrapper] = {}
        self._retrievers            : Dict[str, MongoDBAtlasHybridSearchRetriever] = {}
        self._is_initialized        = False

    async def __aenter__(self) -> Self:
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self) -> Self:
        if self._is_initialized:
            return self

        self.client = AsyncIOMotorClient(
            self.mongodb_uri,
            appname="ovelo-api",
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
        )
        await self.client.admin.command("ping")

        self.database = self.client[self.database_name]
        logger.info(f"Connected to MongoDB database: {self.database_name}")

        self._initialize_collection_wrappers()
        await self._initialize_retrievers()

        self._is_initialized = True
        return self

    async def initialize_all_indexes(self):
        """
        Initialize traditional and vector/hybrid search indexes for all managed collections.
        """
        async def run_init(
            collection_wrapper  : CollectionWrapper,
            collection_type     : str,
            embedding_dim       : Optional[int] = None,
            retriever           : Optional[MongoDBAtlasHybridSearchRetriever] = None,
        ):
            try:
                indexer = MongoIndex(
                    retriever=retriever,
                    collection=collection_wrapper.collection,
                    collection_type=collection_type
                )
                if embedding_dim and retriever:
                    await indexer.create_vector_indexes(
                        embedding_dim=embedding_dim,
                        is_hybrid=True if collection_type == settings.MOVIE_CHUNKS_COLLECTION else False, # todo: remove, currently only movies have hybrid search
                    )
                else:
                    await indexer.create_indexes()
                logger.info(f"Indexes initialized for '{collection_type}'")
            except Exception as e:
                logger.error(f"Failed to initialize indexes for '{collection_type}': {e}")

        tasks = [
            run_init(
                self.movies,
                settings.MOVIES_COLLECTION
            ),
            run_init(
                self.movie_chunks,
                settings.MOVIE_CHUNKS_COLLECTION,
                embedding_dim=settings.MOVIE_NUM_DIMENSIONS,
                retriever=self.movie_chunks_retriever
            ),
            run_init(
                self.tv_shows,
                settings.TV_COLLECTION
            ),
            run_init(
                self.tv_chunks,
                settings.TV_CHUNKS_COLLECTION,
                embedding_dim=settings.TV_NUM_DIMENSIONS,
                retriever=self.tv_chunks_retriever
            )
        ]
        await asyncio.gather(*tasks)
        logger.info("All collection indexes initialized")

    def _initialize_collection_wrappers(self):
        """Initialize all collection wrappers using a helper to avoid duplication."""

        def add_wrapper(key: str, model: Type):
            self._collection_wrappers[key] = CollectionWrapper(
                model=model,
                collection=self.database[key],
                collection_name=key
            )

        # Movie-related collections
        add_wrapper(settings.MOVIES_COLLECTION, MovieDetails)
        add_wrapper(settings.MOVIE_CHUNKS_COLLECTION, dict)
        add_wrapper(settings.MOVIE_WATCH_PROVIDERS_COLLECTION, dict)
        # TV-related collections
        add_wrapper(settings.TV_COLLECTION, TVDetails)
        add_wrapper(settings.TV_SEASONS_COLLECTION, dict)
        add_wrapper(settings.TV_EPISODES_COLLECTION, dict)
        add_wrapper(settings.TV_CHUNKS_COLLECTION, dict)
        add_wrapper(settings.TV_WATCH_PROVIDERS_COLLECTION, dict)

    async def _initialize_retrievers(self):
        """Initialize vector/hybrid search retrievers for chunk collections."""
        if not self.embedding_client or not self.embedding_client.embedding:
            logger.warning("Embedding client not configured. Skipping retriever setup.")
            return

        async def set_retriever(collection_name, text_key, embedding_key, vector_index_name, text_index_name, similarity_metric, top_k):
            vectorstore = MongoDBAtlasVectorSearch.from_connection_string(
                connection_string   = self.mongodb_uri,
                embedding           = self.embedding_client.embedding,
                namespace           = f"{self.database_name}.{collection_name}",
                index_name          = vector_index_name,
                text_key            = text_key,
                embedding_key       = embedding_key,
                relevance_score_fn  = similarity_metric,
            )
            self._retrievers[collection_name] = MongoDBAtlasHybridSearchRetriever(
                vectorstore=vectorstore,
                search_index_name=text_index_name,
                k=top_k,
                oversampling_factor=settings.OVERSAMPLING_FACTOR,
                vector_penalty=settings.VECTOR_PENALTY,
                fulltext_penalty=settings.FULLTEXT_PENALTY
            )

        await asyncio.gather(
            set_retriever(
                settings.MOVIE_CHUNKS_COLLECTION,
                settings.MOVIE_TEXT_PATH,
                settings.MOVIE_EMBEDDING_PATH,
                settings.MOVIE_VECTOR_INDEX_NAME,
                settings.MOVIE_FULLTEXT_INDEX_NAME,
                settings.MOVIE_SIMILARITY,
                settings.RAG_TOP_K
            ),
            set_retriever(
                settings.TV_CHUNKS_COLLECTION,
                settings.TV_TEXT_PATH,
                settings.TV_EMBEDDING_PATH,
                settings.TV_VECTOR_INDEX_NAME,
                settings.TV_FULLTEXT_INDEX_NAME,
                settings.TV_SIMILARITY,
                settings.RAG_TOP_K
            )
        )

    async def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self._is_initialized = False
            logger.debug("Closed MongoDB connection.")


    @property
    def movies(self) -> CollectionWrapper[MovieDetails]:
        return self._collection_wrappers[settings.MOVIES_COLLECTION]

    @property
    def movie_chunks(self) -> CollectionWrapper:
        return self._collection_wrappers[settings.MOVIE_CHUNKS_COLLECTION]

    @property
    def movie_watch_providers(self) -> CollectionWrapper:
        return self._collection_wrappers[settings.MOVIE_WATCH_PROVIDERS_COLLECTION]

    @property
    def tv_shows(self) -> CollectionWrapper[TVDetails]:
        return self._collection_wrappers[settings.TV_COLLECTION]

    @property
    def tv_seasons(self) -> CollectionWrapper:
        return self._collection_wrappers[settings.TV_SEASONS_COLLECTION]

    @property
    def tv_episodes(self) -> CollectionWrapper:
        return self._collection_wrappers[settings.TV_EPISODES_COLLECTION]

    @property
    def tv_chunks(self) -> CollectionWrapper:
        return self._collection_wrappers[settings.TV_CHUNKS_COLLECTION]

    @property
    def tv_watch_providers(self) -> CollectionWrapper:
        return self._collection_wrappers[settings.TV_WATCH_PROVIDERS_COLLECTION]

    # --- Properties for Retriever Access ---
    @property
    def movie_chunks_retriever(self) -> Optional[MongoDBAtlasHybridSearchRetriever]:
        return self._retrievers.get(settings.MOVIE_CHUNKS_COLLECTION)

    @property
    def tv_chunks_retriever(self) -> Optional[MongoDBAtlasHybridSearchRetriever]:
        return self._retrievers.get(settings.TV_CHUNKS_COLLECTION)

    # ---- Vector retrievers for hybrid search ---
    async def perform_hybrid_search(self, query: str) -> List[Document]:
        try:
            # Perform searches in parallel
            movie_task  = self._hybrid_search(self.movie_chunks_retriever,  query)
            tv_task     = self._hybrid_search(self.tv_chunks_retriever,     query)

            results = await asyncio.gather(movie_task, tv_task, return_exceptions=True)
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                for e in errors:
                    logger.error(f"Sub-search failed: {e}")
                raise ValueError("One or more searches failed")

            return [doc for sublist in results for doc in sublist]
        except Exception as err:
            logger.error(f"Error in hybrid search: {err}")
            raise

    async def _hybrid_search(
        self,
        retriever: MongoDBAtlasHybridSearchRetriever,
        query: str
    ) -> List[Document]:
        try:
            if not retriever:
                raise ValueError(
                    "Vector search retriever not initialized for this collection."
                )
            documents: List[Document] = await retriever.ainvoke(query)
            return documents
        except Exception as e:
            logger.error(f"Error performing hybrid search: {e}")
            raise

    # --- High-Level Normalized Data Insertion ---
    async def insert_movie_document(self, movie: MovieDetails) -> str:
        """Insert a movie and all related data into normalized collections."""
        collections = extract_movie_collections(movie)
        movie_id = await self.movies.insert_one(
            collections[settings.MOVIES_COLLECTION]
        )

        # Movie chunks
        chunks = collections[settings.MOVIE_CHUNKS_COLLECTION]
        if chunks:
            for chunk in chunks:
                chunk["movie_id"] = movie_id
            await self.movie_chunks.insert_many(chunks)

        # Movie watch providers
        watch_providers = collections[settings.MOVIE_WATCH_PROVIDERS_COLLECTION]
        if watch_providers:
            watch_providers["movie_id"] = movie_id
            await self.movie_watch_providers.insert_one(watch_providers)

        logger.info(f"Inserted normalized movie data for ID: {movie_id}")
        return movie_id

    async def insert_tv_show_document(self, tv_show: TVDetails) -> str:
        """Insert a TV show and all related data into normalized collections."""
        collections = extract_tv_collections(tv_show)
        tv_show_id = await self.tv_shows.insert_one(
            collections[settings.TV_COLLECTION]
        )

        # Insert seasons and build mapping: (season_number → season_id)
        season_number_to_id = {}
        for season in collections[settings.TV_SEASONS_COLLECTION]:
            season["tv_show_id"] = tv_show_id
            season_id = await self.tv_seasons.insert_one(season)
            season_number_to_id[season["season_number"]] = season_id

        # Insert episodes and build mapping: (season_number, episode_number) → episode_id
        episode_keys_to_id = {}
        for episode in collections[settings.TV_EPISODES_COLLECTION]:
            season_id = season_number_to_id[episode["season_number"]]
            episode["tv_show_id"] = tv_show_id
            episode["season_id"] = season_id
            episode_id = await self.tv_episodes.insert_one(episode)
            episode_keys_to_id[(episode["season_number"], episode["episode_number"])] = episode_id

        # Insert episode chunks
        for chunk in collections[settings.TV_CHUNKS_COLLECTION]:
            ep_key = (chunk["season_number"], chunk["episode_number"])
            episode_id = episode_keys_to_id.get(ep_key)
            if episode_id:
                chunk["tv_show_id"] = tv_show_id
                chunk["episode_id"] = episode_id
                await self.tv_chunks.insert_one(chunk)

        # TV watch providers
        watch_providers = collections[settings.TV_WATCH_PROVIDERS_COLLECTION]
        if watch_providers:
            watch_providers["tv_show_id"] = tv_show_id
            await self.tv_watch_providers.insert_one(watch_providers)

        logger.info(f"Inserted normalized TV show data for ID: {tv_show_id}")
        return tv_show_id

    async def model_exists(self, model_id: int, collection_name: str) -> bool:
        """Check if a document exists in the specified collection."""
        return await self._collection_wrappers[collection_name].find_one({"tmdb_id": model_id}) is not None



async def create_mongo_collections_manager(
    database_name:      str = settings.MONGODB_DB,
    mongodb_uri:        str = settings.MONGODB_URL,
    embedding_client:   Optional[EmbeddingClient] = None,
    initialize_indexes: bool = True
) -> MongoCollectionsManager:
    """
    Factory function to create and initialize a MongoCollectionsManager.
    Usage:
        async with create_mongo_collections_manager(..., initialize_indexes=True) as manager:
            ...
    """
    manager = MongoCollectionsManager(
        database_name=database_name,
        mongodb_uri=mongodb_uri,
        embedding_client=embedding_client
    )
    await manager.initialize()

    if initialize_indexes:
        await manager.initialize_all_indexes()

    return manager