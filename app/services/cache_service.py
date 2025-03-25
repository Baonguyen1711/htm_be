from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)

# Global cache dictionary
test_cache = {}

def get_cached_test(uid: str, test_name: str):

    cache_key = f"{uid}:{test_name}"
    if cache_key in test_cache:
        cached = test_cache[cache_key]
        if time.time() - cached["timestamp"] < 3600:  # 1 hour TTL
            logger.info(f"Cache hit for {cache_key}")
            return cached["data"]
        else:
            logger.info(f"Cache expired for {cache_key}")
            del test_cache[cache_key]
    return None

def set_cached_test(uid: str, test_name: str, data: dict):

    cache_key = f"{uid}:{test_name}"
    test_cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }
    logger.info(f"Cached data for {cache_key}")

def clear_cached_test(uid: str, test_name: str):

    cache_key = f"{uid}:{test_name}"
    if cache_key in test_cache:
        del test_cache[cache_key]
        logger.info(f"Cache cleared for {cache_key}")