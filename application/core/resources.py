from .dependencies import (
    get_embedding_client,
    get_tmdb_client,
    get_opensubtitles_client,
    get_stt_client,
    get_rekognition_client,
    get_mongo_manager,
)

class LazySingleton:
    def __init__(self, getter):
        self.getter = getter
        self._instance = None

    def __getattr__(self, item):
        if self._instance is None:
            self._instance = self.getter()
        return getattr(self._instance, item)

    def __call__(self):
        if self._instance is None:
            self._instance = self.getter()
        return self._instance

class AsyncLazySingleton:
    def __init__(self, async_getter):
        self.async_getter = async_getter
        self._instance = None
        self._lock = None

    async def __call__(self):
        if self._instance is None:
            if self._lock is None:
                import asyncio
                self._lock = asyncio.Lock()
            async with self._lock:
                if self._instance is None:
                    self._instance = await self.async_getter()
        return self._instance

    def __getattr__(self, item):
        raise AttributeError(
            f"AsyncLazySingleton requires await: await {self.__class__.__name__}()"
        )

# Sync resources (singletons)
embedding_client     = LazySingleton(get_embedding_client)
stt_client           = LazySingleton(get_stt_client)
tmdb_client          = LazySingleton(get_tmdb_client)
opensubtitles_client = LazySingleton(get_opensubtitles_client)
rekognition_client   = LazySingleton(get_rekognition_client)

# Async resources: MongoCollectionsManager
mongo_manager        = AsyncLazySingleton(get_mongo_manager)

__all__ = [
    "mongo_manager",
    "embedding_client",
    "stt_client",
    "tmdb_client",
    "opensubtitles_client",
    "rekognition_client",
]
