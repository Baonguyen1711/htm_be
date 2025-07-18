import traceback
import logging
from fastapi import HTTPException
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

def handle_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error in route {func.__name__}: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    return wrapper