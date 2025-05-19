from .settings import Settings
from .dependencies import get_http_client
from dotenv import load_dotenv

load_dotenv()

# Create a singleton instance
Settings()

__all__ = ['Settings', 'get_http_client']
