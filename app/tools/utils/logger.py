"""
Logger - Loguru-based structured logging
"""
import sys
from loguru import logger

def setup_logger():
    """Configure loguru logger with custom format"""
    from app.config.settings import get_settings
    settings = get_settings()
    
    # Remove default handler
    logger.remove()
    
    # Add custom handler with colored output (enqueue=True for async safety)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=settings.log_level,
        colorize=True,
        enqueue=True
    )
    
    return logger


def get_logger(name: str = "app"):
    """Get a named logger instance"""
    return logger.bind(name=name)


# Initialize logger on import
app_logger = setup_logger()
