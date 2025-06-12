from .tv import TVDocumentBuilder
from .movie import MovieDocumentBuilder


# Create document builders
movie_document = MovieDocumentBuilder()
tv_document = TVDocumentBuilder()

__all__ = [
    "movie_document",
    "tv_document"
]