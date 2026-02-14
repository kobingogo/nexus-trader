
import time
import functools
import logging
from typing import Any, Callable, Dict, Tuple

logger = logging.getLogger(__name__)

def ttl_cache(ttl: int = 60):
    """
    Simple TTL cache decorator.
    :param ttl: Time to live in seconds.
    Storage is per function instance closure.
    """
    def decorator(func: Callable):
        cache: Dict[Any, Tuple[Any, float]] = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Compute cache key from arguments
            # Convert args to tuple (hashable), handle dict kwargs (frozenset)
            try:
                key = (args, frozenset(kwargs.items()))
            except TypeError:
                # If args/kwargs are not hashable (e.g. lists), bypass cache
                logger.warning(f"Unhashable args in {func.__name__}, bypassing cache.")
                return func(*args, **kwargs)

            now = time.time()
            cached_val = cache.get(key)
            
            if cached_val:
                data, timestamp = cached_val
                if now - timestamp < ttl:
                    return data
            
            # Cache miss or expired
            try:
                result = func(*args, **kwargs)
                cache[key] = (result, now)
                return result
            except Exception as e:
                logger.error(f"Error fetching data in {func.__name__}: {e}")
                # Fallback: return stale data if available
                if cached_val:
                    logger.warning(f"Returning stale cache for {func.__name__}")
                    return cached_val[0]
                raise e # Or return default?
        
        return wrapper
    return decorator

class SimpleCache:
    """
    Simple in-memory cache with expiry.
    """
    _data = {}
    _expiry = {}

    @classmethod
    def get(cls, key: str) -> Any:
        if key in cls._data and time.time() < cls._expiry.get(key, 0):
            return cls._data[key]
        return None

    @classmethod
    def set(cls, key: str, value: Any, ttl: int = 60):
        cls._data[key] = value
        cls._expiry[key] = time.time() + ttl
