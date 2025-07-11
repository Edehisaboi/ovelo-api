from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import Dict, Any

from application.models.media import MovieDetails, TVDetails
from application.core.config import settings


class DocumentBuilder(ABC):
    """Abstract base class for building documents for database storage."""

    @abstractmethod
    def build(self, model: Any) -> Dict[str, Any]:
        """Build a document from a model instance."""
        pass


class MovieDocumentBuilder(DocumentBuilder):
    """Builder for movie documents."""

    def build(self, movie: MovieDetails) -> Dict[str, Any]:
        """Build a movie document for database storage."""
        doc = movie.model_dump()
        
        # Add metadata
        doc["media_type"] = "movie"
        doc["created_at"] = datetime.now(UTC)
        doc["updated_at"] = datetime.now(UTC)
        doc["embedding_model"] = settings.OPENAI_EMBEDDING_MODEL

        return doc


class TVDocumentBuilder(DocumentBuilder):
    """Builder for TV show documents."""

    def build(self, tv: TVDetails) -> Dict[str, Any]:
        """Build a TV show document for database storage."""
        doc = tv.model_dump()
        
        # Add metadata
        doc["media_type"] = "tv"
        doc["created_at"] = datetime.now(UTC)
        doc["updated_at"] = datetime.now(UTC)
        doc["embedding_model"] = settings.OPENAI_EMBEDDING_MODEL
        
        return doc
