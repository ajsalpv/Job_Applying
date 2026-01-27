"""
Logger - Loguru-based structured logging
"""
import os
from loguru import logger
from app.config.settings import get_settings


def setup_logger():
    """Configure loguru logger with custom format"""
    settings = get_settings()
    
    # Ensure logs directory exists to prevent crash in Docker/Linux
    os.makedirs("logs", exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add custom handler with colored output
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # Add file handler for persistent logs
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )
    
    return logger


def get_logger(name: str = "app"):
    """Get a named logger instance"""
    return logger.bind(name=name)


# Initialize logger on import
app_logger = setup_logger()
