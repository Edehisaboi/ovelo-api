from api.services.database.index import setup_indexes
from ..document.movie import MovieDocumentBuilder
from ..document.tv import TVDocumentBuilder

# Create document builders
movie_document = MovieDocumentBuilder()
tv_document = TVDocumentBuilder()

async def index_database():
    """Initialize the database indexes for both collections."""
    await setup_indexes()

__all__ = [
    # Functions
    'index_database',
    # Classes
    'movie_document', 'tv_document'
]
