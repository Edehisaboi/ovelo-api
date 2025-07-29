from loguru import logger

from application.core.config import settings
from pathlib import Path

def setup_logging():
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / settings.LOG_FILE

    logger.remove()
    # File logging with rotation/retention
    logger.add(
        log_file,
        rotation=settings.LOG_MAX_BYTES,
        retention=settings.LOG_BACKUP_COUNT,
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {module}:{function}:{line} - {message}",
        encoding='utf-8'
    )
    # Console logging: just add it—no lambda! Loguru handles the coloring/format
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        # You can use Loguru's colorful default or provide a format (colors are supported)
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}:{function}:{line}</cyan> - <level>{message}</level>"
    )
    return logger

def get_logger(name: str):
    return logger.bind(module=name)

# Ensure sys is imported for sys.stderr
import sys

setup_logging()

__all__ = ['setup_logging', 'get_logger', 'logger']
