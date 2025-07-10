from .dependencies import (
    get_movie_db,
    get_tv_db,
    get_embedding_client,
    get_tmdb_client,
    get_opensubtitles_client,
    get_stt_client,
    get_rekognition_client,
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

movie_db             = LazySingleton(get_movie_db)
tv_db                = LazySingleton(get_tv_db)
embedding_client     = LazySingleton(get_embedding_client)
stt_client           = LazySingleton(get_stt_client)
tmdb_client          = LazySingleton(get_tmdb_client)
opensubtitles_client = LazySingleton(get_opensubtitles_client)
rekognition_client   = LazySingleton(get_rekognition_client)

__all__ = [
    "movie_db",
    "tv_db",
    "embedding_client",
    "stt_client",
    "tmdb_client",
    "opensubtitles_client",
    "rekognition_client",
]
