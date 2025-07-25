import json
import redis.asyncio as redis
from typing import Any, Optional, Dict
from app.config import settings


class CacheManager:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection with lazy initialization."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await self._redis.ping()
            except Exception as e:
                print(f"Redis connection failed: {str(e)}")
                self._redis = None
        return self._redis
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return None
            
            value = await redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int) -> bool:
        """Set value in cache with TTL."""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return False
            
            json_value = json.dumps(value, default=str)
            await redis_client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return False
            
            result = await redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return False
            
            result = await redis_client.exists(key)
            return result > 0
        except Exception as e:
            print(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


# Global cache instance
cache_manager = CacheManager()