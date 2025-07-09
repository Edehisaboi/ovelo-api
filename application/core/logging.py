from loguru import logger
from application.core.config import settings
from pathlib import Path

def setup_logging():
    """
    Set up loguru logging configuration for the application.
    Creates a log directory if it doesn't exist and configures loguru handlers.
    """
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / settings.LOG_FILE

    logger.remove()
    # Use loguru format syntax for file logging
    logger.add(
        log_file, 
        rotation=settings.LOG_MAX_BYTES, 
        retention=settings.LOG_BACKUP_COUNT, 
        level=settings.LOG_LEVEL, 
        format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}", 
        encoding='utf-8'
    )
    # Use loguru format syntax for console output
    logger.add(
        lambda msg: print(msg, end=''), 
        level=settings.LOG_LEVEL, 
        format="{time:HH:mm:ss} - {level} - {message}"
    )
    return logger

def get_logger(name: str):
    """
    Get a loguru logger instance for a specific module.
    Args:
        name: Name of the module (usually __name__)
    Returns:
        loguru.Logger: Configured logger instance
    """
    return logger.bind(module=name)

# Initialize logging when a module is imported
setup_logging()

__all__ = ['setup_logging', 'get_logger', 'logger'] 