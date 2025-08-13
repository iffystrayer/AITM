"""
Redis configuration for threat intelligence caching
"""

import redis.asyncio as redis
from typing import Optional, Any, Dict, List
import json
import pickle
from datetime import datetime, timedelta
from app.core.config import get_settings

settings = get_settings()


class RedisManager:
    """Redis connection and caching manager for threat intelligence"""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        self._redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._redis
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
    
    async def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set JSON value in Redis with optional expiration"""
        try:
            redis_client = await self.get_redis()
            json_value = json.dumps(value, default=str)
            if expire:
                return await redis_client.setex(key, expire, json_value)
            else:
                return await redis_client.set(key, json_value)
        except Exception as e:
            print(f"Redis set_json error: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis"""
        try:
            redis_client = await self.get_redis()
            value = await redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get_json error: {e}")
            return None
    
    async def set_pickle(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set pickled value in Redis with optional expiration"""
        try:
            redis_client = await self.get_redis()
            pickled_value = pickle.dumps(value)
            if expire:
                return await redis_client.setex(key, expire, pickled_value)
            else:
                return await redis_client.set(key, pickled_value)
        except Exception as e:
            print(f"Redis set_pickle error: {e}")
            return False
    
    async def get_pickle(self, key: str) -> Optional[Any]:
        """Get pickled value from Redis"""
        try:
            redis_client = await self.get_redis()
            # Need to use get with decode_responses=False for binary data
            redis_binary = redis.from_url(self.redis_url, decode_responses=False)
            value = await redis_binary.get(key)
            await redis_binary.close()
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"Redis get_pickle error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            redis_client = await self.get_redis()
            return bool(await redis_client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            redis_client = await self.get_redis()
            return bool(await redis_client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            redis_client = await self.get_redis()
            return bool(await redis_client.expire(key, seconds))
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in Redis"""
        try:
            redis_client = await self.get_redis()
            return await redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return None
    
    async def set_hash(self, key: str, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set hash in Redis"""
        try:
            redis_client = await self.get_redis()
            # Convert values to strings
            str_mapping = {k: json.dumps(v, default=str) for k, v in mapping.items()}
            result = await redis_client.hset(key, mapping=str_mapping)
            if expire:
                await redis_client.expire(key, expire)
            return bool(result)
        except Exception as e:
            print(f"Redis set_hash error: {e}")
            return False
    
    async def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get hash from Redis"""
        try:
            redis_client = await self.get_redis()
            hash_data = await redis_client.hgetall(key)
            if hash_data:
                # Convert back from JSON strings
                return {k: json.loads(v) for k, v in hash_data.items()}
            return None
        except Exception as e:
            print(f"Redis get_hash error: {e}")
            return None
    
    async def add_to_set(self, key: str, *values: str) -> int:
        """Add values to Redis set"""
        try:
            redis_client = await self.get_redis()
            return await redis_client.sadd(key, *values)
        except Exception as e:
            print(f"Redis add_to_set error: {e}")
            return 0
    
    async def get_set_members(self, key: str) -> set:
        """Get all members of Redis set"""
        try:
            redis_client = await self.get_redis()
            return await redis_client.smembers(key)
        except Exception as e:
            print(f"Redis get_set_members error: {e}")
            return set()
    
    async def is_set_member(self, key: str, value: str) -> bool:
        """Check if value is member of Redis set"""
        try:
            redis_client = await self.get_redis()
            return bool(await redis_client.sismember(key, value))
        except Exception as e:
            print(f"Redis is_set_member error: {e}")
            return False


# Global Redis manager instance
redis_manager = RedisManager()


class ThreatIntelligenceCache:
    """Specialized caching for threat intelligence data"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.default_ttl = 3600  # 1 hour
        self.long_ttl = 86400    # 24 hours
    
    async def cache_threat_indicator(self, indicator_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache threat indicator data"""
        key = f"threat_indicator:{indicator_id}"
        return await self.redis.set_json(key, data, ttl or self.default_ttl)
    
    async def get_threat_indicator(self, indicator_id: int) -> Optional[Dict[str, Any]]:
        """Get cached threat indicator data"""
        key = f"threat_indicator:{indicator_id}"
        return await self.redis.get_json(key)
    
    async def cache_feed_status(self, feed_id: int, status: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache threat feed status"""
        key = f"feed_status:{feed_id}"
        return await self.redis.set_json(key, status, ttl or self.default_ttl)
    
    async def get_feed_status(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """Get cached threat feed status"""
        key = f"feed_status:{feed_id}"
        return await self.redis.get_json(key)
    
    async def cache_correlation_results(self, project_id: int, results: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Cache threat correlation results for a project"""
        key = f"correlations:{project_id}"
        return await self.redis.set_json(key, results, ttl or self.default_ttl)
    
    async def get_correlation_results(self, project_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached threat correlation results"""
        key = f"correlations:{project_id}"
        return await self.redis.get_json(key)
    
    async def cache_search_results(self, query_hash: str, results: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache threat search results"""
        key = f"search:{query_hash}"
        return await self.redis.set_json(key, results, ttl or self.default_ttl)
    
    async def get_search_results(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached threat search results"""
        key = f"search:{query_hash}"
        return await self.redis.get_json(key)
    
    async def cache_analytics_data(self, analytics_type: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache threat analytics data"""
        key = f"analytics:{analytics_type}"
        return await self.redis.set_json(key, data, ttl or self.long_ttl)
    
    async def get_analytics_data(self, analytics_type: str) -> Optional[Dict[str, Any]]:
        """Get cached threat analytics data"""
        key = f"analytics:{analytics_type}"
        return await self.redis.get_json(key)
    
    async def invalidate_project_cache(self, project_id: int) -> bool:
        """Invalidate all cached data for a project"""
        try:
            keys_to_delete = [
                f"correlations:{project_id}",
                f"project_threats:{project_id}",
                f"project_analytics:{project_id}"
            ]
            
            for key in keys_to_delete:
                await self.redis.delete(key)
            
            return True
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return False
    
    async def track_feed_processing(self, feed_id: int, status: str) -> bool:
        """Track feed processing status"""
        key = f"feed_processing:{feed_id}"
        data = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.redis.set_json(key, data, 3600)  # 1 hour TTL
    
    async def get_feed_processing_status(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """Get feed processing status"""
        key = f"feed_processing:{feed_id}"
        return await self.redis.get_json(key)


# Global threat intelligence cache instance
threat_cache = ThreatIntelligenceCache(redis_manager)