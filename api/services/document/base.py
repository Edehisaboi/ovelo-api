from abc import ABC, abstractmethod
from typing import Dict, Any, Generic, TypeVar
from datetime import datetime, timezone

T = TypeVar('T')

class DocumentBuilder(Generic[T], ABC):
    """Base interface for document builders."""
    
    def __init__(self):
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = self._created_at
    
    @abstractmethod
    def build(self, data: T) -> Dict[str, Any]:
        """Build a document from the given data."""
        pass
    
    def _get_base_document(self) -> Dict[str, Any]:
        """Get the base document fields."""
        return {
            "created_at": self._created_at,
            "updated_at": self._updated_at
        }
    
    def _update_timestamp(self) -> None:
        """Update the document timestamp."""
        self._updated_at = datetime.now(timezone.utc) 