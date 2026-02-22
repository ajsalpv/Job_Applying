"""
Logger - Loguru-based structured logging
"""
import sys
from loguru import logger

_initialized = False

def get_logger(name: str = "app"):
    """Get a named logger instance"""
    if not _initialized:
        setup_logger()
    return logger.bind(name=name)


def setup_logger():
    """Configure loguru logger with custom format"""
    global _initialized
    if _initialized:
        return logger
        
    try:
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
            level=settings.log_level if hasattr(settings, 'log_level') else "INFO",
            colorize=True,
            enqueue=True
        )
        _initialized = True
    except Exception:
        # Fallback if settings fail
        pass
        
    return logger
