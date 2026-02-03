"""
Retry utilities - Tenacity-based retry logic
"""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import requests
from app.tools.utils.logger import get_logger

logger = get_logger("retry")


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    exceptions: tuple = (Exception,),
):
    """
    Create a configurable retry decorator.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exceptions: Tuple of exceptions to retry on
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, log_level=20),  # INFO level
    )


# Pre-configured decorators for common use cases
llm_retry = create_retry_decorator(
    max_attempts=3,
    min_wait=2,
    max_wait=30,
    exceptions=(Exception,),
)

browser_retry = create_retry_decorator(
    max_attempts=2,
    min_wait=5,
    max_wait=15,
    exceptions=(TimeoutError, ConnectionError),
)

sheets_retry = create_retry_decorator(
    max_attempts=3,
    min_wait=1,
    max_wait=10,
    exceptions=(Exception,),
)

telegram_retry = create_retry_decorator(
    max_attempts=3,
    min_wait=2,
    max_wait=10,
    exceptions=(IOError, requests.RequestException),
)
