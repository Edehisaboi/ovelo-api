import logging
import logging.handlers
from pathlib import Path
from config import Settings

def setup_logging():
    """
    Set up centralized logging configuration for the application.
    Creates log directory if it doesn't exist and configures logging handlers.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(Settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(Settings.LOG_LEVEL)
    
    # Clear any existing handlers
    root_logger.handlers = []
    
    # Create formatters
    file_formatter = logging.Formatter(Settings.LOG_FORMAT)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / Settings.LOG_FILE,
        maxBytes=Settings.LOG_MAX_BYTES,
        backupCount=Settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(Settings.LOG_LEVEL)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(Settings.LOG_LEVEL)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set logging level for specific modules
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)

# Initialize logging when module is imported
logger = setup_logging()

__all__ = ['setup_logging', 'get_logger', 'logger'] 