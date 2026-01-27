from typing import Optional, Any, Union
from redis import Redis, ConnectionPool, ConnectionError
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from .config import settings
from loguru import logger
import json
import pickle
import hashlib
import time
from datetime import datetime

class CacheManager:
    """Manager class for Redis cache operations."""
    
    _instance: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None
    
    @classmethod
    def get_instance(cls) -> Redis:
        """Get Redis instance (singleton pattern) with connection pooling."""
        if cls._instance is None:
            if cls._pool is None:
                # Create connection pool
                cls._pool = ConnectionPool(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_timeout=settings.REDIS_TIMEOUT,
                    socket_connect_timeout=settings.REDIS_TIMEOUT,
                    max_connections=50  # Adjust based on your needs
                )
            
            # Create Redis instance with retry logic
            retry = Retry(ExponentialBackoff(), 3)
            cls._instance = Redis(
                connection_pool=cls._pool,
                retry=retry,
                health_check_interval=30
            )
            
        return cls._instance

    @classmethod
    def close(cls):
        """Close Redis connection and pool."""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
        if cls._pool:
            cls._pool.disconnect()
            cls._pool = None

class CacheSerializer:
    """Serializer for cache data."""
    
    @staticmethod
    def serialize(data: Any) -> str:
        """Serialize data to string."""
        if isinstance(data, (str, int, float, bool)):
            return json.dumps(data)
        return pickle.dumps(data).hex()
    
    @staticmethod
    def deserialize(data: str) -> Any:
        """Deserialize data from string."""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            try:
                return pickle.loads(bytes.fromhex(data))
            except:
                return data

class CacheKey:
    """Cache key generator with namespacing."""
    
    @staticmethod
    def build(
        namespace: str,
        key_parts: Union[str, list],
        version: str = "v1"
    ) -> str:
        """Build cache key with namespace and version."""
        if isinstance(key_parts, list):
            key_parts = ":".join(str(part) for part in key_parts)
        
        # Create hash of the key parts
        key_hash = hashlib.md5(key_parts.encode()).hexdigest()
        
        return f"cache:{version}:{namespace}:{key_hash}"

async def init_cache():
    """Initialize FastAPI cache with Redis backend."""
    try:
        redis_instance = CacheManager.get_instance()
        
        # Test connection
        redis_instance.ping()
        
        # Initialize FastAPI cache
        FastAPICache.init(
            backend=RedisBackend(redis_instance),
            prefix="fastapi-cache",
            expire=settings.CACHE_EXPIRE_IN_SECONDS,
            key_builder=cache_key_builder,
            serializer=CacheSerializer,
        )
        
        logger.info("Cache initialized successfully")
        
    except ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize cache: {str(e)}")
        raise

async def clear_cache(pattern: str = "*", namespace: Optional[str] = None):
    """Clear cache entries matching pattern."""
    try:
        redis_instance = CacheManager.get_instance()
        
        # Build pattern with namespace
        if namespace:
            pattern = f"cache:*:{namespace}:{pattern}"
        else:
            pattern = f"cache:*:{pattern}"
        
        # Use scan instead of keys for large datasets
        cursor = 0
        deleted_keys = 0
        while True:
            cursor, keys = redis_instance.scan(cursor, pattern, 100)
            if keys:
                redis_instance.delete(*keys)
                deleted_keys += len(keys)
            if cursor == 0:
                break
        
        logger.info(f"Cleared {deleted_keys} cache entries matching pattern: {pattern}")
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise

async def get_cache_stats():
    """Get cache statistics."""
    try:
        redis_instance = CacheManager.get_instance()
        info = redis_instance.info()
        
        # Get memory usage by pattern
        stats = {
            "total_keys": 0,
            "memory_by_namespace": {},
            "keys_by_namespace": {},
            "system": {
                "used_memory": info["used_memory_human"],
                "connected_clients": info["connected_clients"],
                "uptime_days": info["uptime_in_days"],
                "hit_rate": _calculate_hit_rate(info),
                "fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
            }
        }
        
        # Scan all keys and group by namespace
        cursor = 0
        while True:
            cursor, keys = redis_instance.scan(cursor, "cache:*", 100)
            if keys:
                for key in keys:
                    namespace = key.split(":")[2]
                    stats["total_keys"] += 1
                    stats["keys_by_namespace"][namespace] = stats["keys_by_namespace"].get(namespace, 0) + 1
                    
                    # Get memory usage for key
                    memory = redis_instance.memory_usage(key)
                    if memory:
                        stats["memory_by_namespace"][namespace] = stats["memory_by_namespace"].get(namespace, 0) + memory
            
            if cursor == 0:
                break
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise

def _calculate_hit_rate(info: dict) -> float:
    """Calculate cache hit rate."""
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses
    return (hits / total * 100) if total > 0 else 0

def cache_key_builder(
    func,
    namespace: Optional[str] = None,
    *args,
    **kwargs
) -> str:
    """Custom cache key builder with versioning and namespacing."""
    # Get function module and name
    key_parts = [
        func.__module__,
        func.__name__,
    ]
    
    # Add args and kwargs
    if args:
        key_parts.extend(str(arg) for arg in args)
    if kwargs:
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # Use namespace from function if not provided
    if namespace is None:
        namespace = func.__module__.split(".")[-1]
    
    return CacheKey.build(namespace, key_parts)
