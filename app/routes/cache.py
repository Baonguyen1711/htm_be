from fastapi import APIRouter
from ..services.cache_service import get_cache_stats, cleanup_expired_cache, clear_all_cache
from ..helper.exception import handle_exceptions
import logging

logger = logging.getLogger(__name__)

class CacheRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/cache")
        
        self.router.get("/stats")(self.get_cache_stats)
        self.router.post("/cleanup")(self.cleanup_cache)
        self.router.post("/clear")(self.clear_cache)
    
    @handle_exceptions
    def get_cache_stats(self):
        """Get cache statistics"""
        stats = get_cache_stats()
        return {
            "cache_stats": stats,
            "message": f"Cache contains {stats['size']} entries"
        }
    
    @handle_exceptions
    def cleanup_cache(self):
        """Manually trigger cache cleanup"""
        cleaned_count = cleanup_expired_cache()
        return {
            "message": f"Cleaned up {cleaned_count} expired cache entries"
        }
    
    @handle_exceptions
    def clear_cache(self):
        """Clear all cache entries (use with caution!)"""
        clear_all_cache()
        return {
            "message": "All cache entries cleared"
        }
