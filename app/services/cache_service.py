from collections import OrderedDict
import time
import logging
import threading
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LRUCache:
    """Thread-safe LRU Cache with TTL support"""

    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None

            # Check if expired
            entry = self.cache[key]
            if time.time() - entry["timestamp"] > entry["ttl"]:
                logger.info(f"Cache expired for {key}")
                del self.cache[key]
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            logger.info(f"Cache hit for {key}")
            return entry["data"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self.lock:
            # Use default TTL if not specified
            ttl = ttl or self.default_ttl

            # Remove oldest entries if cache is full
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                logger.info(f"Evicting oldest cache entry: {oldest_key}")
                del self.cache[oldest_key]

            self.cache[key] = {
                "data": value,
                "timestamp": time.time(),
                "ttl": ttl
            }
            logger.info(f"Cached data for {key}")

    def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.info(f"Cache cleared for {key}")
                return True
            return False

    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared completely")

    def size(self) -> int:
        with self.lock:
            return len(self.cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time - entry["timestamp"] > entry["ttl"]
            ]

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)

# Global cache instance
# Configure via environment variables
MAX_CACHE_SIZE = int(os.getenv("CACHE_MAX_SIZE", "100"))
DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1 hour

test_cache = LRUCache(max_size=MAX_CACHE_SIZE, default_ttl=DEFAULT_TTL)

def get_cached_test(uid: str, test_name: str) -> Optional[Dict]:
    """Get cached test data for a user"""
    cache_key = f"{uid}:{test_name}"
    return test_cache.get(cache_key)

def set_cached_test(uid: str, test_name: str, data: dict, ttl: Optional[int] = None) -> None:
    """Cache test data for a user with optional custom TTL"""
    cache_key = f"{uid}:{test_name}"
    test_cache.set(cache_key, data, ttl)

def clear_cached_test(uid: str, test_name: str) -> bool:
    """Clear cached test data for a user"""
    cache_key = f"{uid}:{test_name}"
    return test_cache.delete(cache_key)

def clear_all_cache() -> None:
    """Clear all cached data"""
    test_cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        "size": test_cache.size(),
        "max_size": test_cache.max_size,
        "default_ttl": test_cache.default_ttl
    }

def cleanup_expired_cache() -> int:
    """Manually cleanup expired entries"""
    return test_cache.cleanup_expired()

# Background cleanup task
import asyncio
from contextlib import asynccontextmanager

async def periodic_cache_cleanup():
    """Background task to periodically clean up expired cache entries"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            cleanup_expired_cache()
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")

# Optional: Add this to your FastAPI startup
@asynccontextmanager
async def cache_lifespan(app):
    """Lifespan context manager for cache cleanup"""
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cache_cleanup())
    try:
        yield
    finally:
        # Cancel cleanup task on shutdown
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass