import uvicorn
from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    try:
        logger.info("Starting Ovelo-API server...")
        logger.info(f"Debug mode: {settings.DEBUG_MODE}")
        logger.info(f"Log level: {settings.LOG_LEVEL}")
        
        uvicorn.run(
            "application.app:application",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG_MODE,
            log_level=settings.LOG_LEVEL.lower()
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
