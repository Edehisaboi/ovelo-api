from .document import (
    DocumentBuilder,
    MovieDocumentBuilder,
    TVDocumentBuilder
)

# Create singleton instances
movie_document = MovieDocumentBuilder()
tv_document = TVDocumentBuilder()

__all__ = [
    "DocumentBuilder",
    "MovieDocumentBuilder",
    "TVDocumentBuilder",

    "movie_document",
    "tv_document"
] 