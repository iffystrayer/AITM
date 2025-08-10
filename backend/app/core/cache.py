"""
Cache Manager for AITM

Provides caching functionality for analytics, API responses, and performance optimization.
Supports Redis backend with fallback to in-memory caching.
"""

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import hashlib
import pickle
import os

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class InMemoryCache:
    """Fallback in-memory cache implementation"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._max_size = 1000
        self._cleanup_task = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry['expires_at'] and datetime.utcnow() > entry['expires_at']:
            del self._cache[key]
            return None
        
        return entry['value']
    
    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set value in cache with expiration"""
        try:
            # Clean up if cache is too large
            if len(self._cache) >= self._max_size:
                await self._cleanup()
            
            expires_at = datetime.utcnow() + timedelta(seconds=expire) if expire > 0 else None
            
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.utcnow()
            }
            return True
        except Exception as e:
            logger.error(f"Error setting cache value: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear all cache entries"""
        self._cache.clear()
        return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return await self.get(key) is not None
    
    async def _cleanup(self):
        """Clean up expired entries and limit cache size"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry['expires_at'] and now > entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        # If still too large, remove oldest entries
        if len(self._cache) >= self._max_size:
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1]['created_at']
            )
            
            num_to_remove = len(self._cache) - int(self._max_size * 0.8)
            for key, _ in sorted_items[:num_to_remove]:
                del self._cache[key]

class RedisCache:
    """Redis-backed cache implementation"""
    
    def __init__(self, url: str = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[redis.Redis] = None
        self.connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(self.url, decode_responses=False)
            await self.redis.ping()
            self.connected = True
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.connected:
            return None
        
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    return pickle.loads(value)
                except Exception:
                    return value.decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting cache value: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set value in Redis cache with expiration"""
        if not self.connected:
            return False
        
        try:
            # Try to serialize as JSON first, then pickle
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value)
            
            await self.redis.set(key, serialized_value, ex=expire if expire > 0 else None)
            return True
        except Exception as e:
            logger.error(f"Error setting cache value: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache"""
        if not self.connected:
            return False
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting cache value: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries (use with caution)"""
        if not self.connected:
            return False
        
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.connected:
            return False
        
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error checking cache key existence: {e}")
            return False

class CacheManager:
    """Main cache manager with fallback support"""
    
    def __init__(self, use_redis: bool = True, redis_url: str = None):
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.redis_cache = RedisCache(redis_url) if self.use_redis else None
        self.memory_cache = InMemoryCache()
        self.initialized = False
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Initialize cache manager"""
        if self.initialized:
            return
        
        if self.use_redis:
            try:
                await self.redis_cache.connect()
                logger.info("Cache manager initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to memory cache: {e}")
                self.use_redis = False
        
        if not self.use_redis:
            logger.info("Cache manager initialized with memory backend")
        
        self.initialized = True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Try Redis first if available
            if self.use_redis:
                value = await self.redis_cache.get(key)
                if value is not None:
                    self.stats['hits'] += 1
                    return value
            
            # Fallback to memory cache
            value = await self.memory_cache.get(key)
            if value is not None:
                self.stats['hits'] += 1
                return value
            
            self.stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache value: {e}")
            self.stats['errors'] += 1
            return None
    
    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set value in cache"""
        if not self.initialized:
            await self.initialize()
        
        success = False
        
        try:
            # Try Redis first if available
            if self.use_redis:
                success = await self.redis_cache.set(key, value, expire)
            
            # Always set in memory cache as backup
            memory_success = await self.memory_cache.set(key, value, expire)
            success = success or memory_success
            
            if success:
                self.stats['sets'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting cache value: {e}")
            self.stats['errors'] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.initialized:
            await self.initialize()
        
        success = False
        
        try:
            # Delete from both Redis and memory
            if self.use_redis:
                redis_success = await self.redis_cache.delete(key)
                success = redis_success
            
            memory_success = await self.memory_cache.delete(key)
            success = success or memory_success
            
            if success:
                self.stats['deletes'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting cache value: {e}")
            self.stats['errors'] += 1
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries"""
        if not self.initialized:
            await self.initialize()
        
        success = False
        
        try:
            if self.use_redis:
                redis_success = await self.redis_cache.clear()
                success = redis_success
            
            memory_success = await self.memory_cache.clear()
            success = success or memory_success
            
            return success
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            self.stats['errors'] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.initialized:
            await self.initialize()
        
        try:
            if self.use_redis:
                if await self.redis_cache.exists(key):
                    return True
            
            return await self.memory_cache.exists(key)
            
        except Exception as e:
            logger.error(f"Error checking cache key existence: {e}")
            self.stats['errors'] += 1
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'backend': 'redis' if self.use_redis else 'memory',
            'initialized': self.initialized,
            'stats': self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests
        }
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments"""
        # Create a consistent string representation
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def cached(self, key: str, expire: int = 300):
        """Decorator for caching function results"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Check cache first
                cached_result = await self.get(key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(key, result, expire)
                return result
            
            return wrapper
        return decorator
    
    async def close(self):
        """Close cache connections"""
        if self.use_redis and self.redis_cache:
            await self.redis_cache.disconnect()

# Global cache manager instance
cache_manager = CacheManager()

# Dependency for FastAPI
def get_cache_manager() -> CacheManager:
    """Dependency to get cache manager instance"""
    return cache_manager

# Cache decorators
def cache_result(key_prefix: str = "", expire: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{cache_manager.generate_cache_key(*args, **kwargs)}"
            
            # Check cache
            result = await cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute and cache
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, expire)
            return result
        
        return wrapper
    return decorator

# Analytics-specific cache utilities
class AnalyticsCache:
    """Specialized caching for analytics data"""
    
    @staticmethod
    async def get_dashboard_cache_key(user_id: int, days: int, **params) -> str:
        """Generate cache key for dashboard metrics"""
        return f"dashboard:{user_id}:{days}:{hash(str(sorted(params.items())))}"
    
    @staticmethod
    async def get_project_cache_key(project_id: int, **params) -> str:
        """Generate cache key for project analytics"""
        return f"project:{project_id}:{hash(str(sorted(params.items())))}"
    
    @staticmethod
    async def invalidate_user_cache(user_id: int):
        """Invalidate all cache entries for a user"""
        # This would be implemented with pattern matching in Redis
        # For now, we'll clear specific known patterns
        patterns = [
            f"dashboard:{user_id}:*",
            f"user:{user_id}:*"
        ]
        
        # In a real implementation, you'd use Redis SCAN with patterns
        logger.info(f"Would invalidate cache patterns for user {user_id}: {patterns}")
    
    @staticmethod
    async def invalidate_project_cache(project_id: int):
        """Invalidate cache entries for a specific project"""
        patterns = [f"project:{project_id}:*"]
        logger.info(f"Would invalidate cache patterns for project {project_id}: {patterns}")
