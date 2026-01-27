from functools import wraps
from typing import Optional, Callable, Any
from .cache import CacheManager, CacheKey, CacheSerializer
from .config import settings
import inspect
import asyncio
from loguru import logger

def cached(
    namespace: Optional[str] = None,
    expire: Optional[int] = None,
    key_builder: Optional[Callable] = None,
    skip_cache: Optional[Callable] = None,
    cache_null: Optional[bool] = None
):
    """
    Cache decorator for service methods.
    
    Args:
        namespace: Cache namespace. Defaults to function's module name.
        expire: Cache expiration time in seconds. Defaults to CACHE_DEFAULT_TIMEOUT.
        key_builder: Custom key builder function. Defaults to default key builder.
        skip_cache: Function to determine if caching should be skipped.
        cache_null: Whether to cache None values. Defaults to CACHE_NULL_VALUES.
    """
    def decorator(func):
        # Get function signature
        sig = inspect.signature(func)
        
        # Determine if function is async
        is_async = asyncio.iscoroutinefunction(func)
        
        # Get cache settings
        _expire = expire or settings.CACHE_DEFAULT_TIMEOUT
        _cache_null = cache_null if cache_null is not None else settings.CACHE_NULL_VALUES
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            # Check if caching should be skipped
            if skip_cache and skip_cache(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(func, *args, **kwargs)
            else:
                # Bind arguments to signature
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Build key parts
                key_parts = [
                    func.__module__,
                    func.__name__,
                    str(bound_args.arguments)
                ]
                
                # Use namespace from decorator or function's module
                _namespace = namespace or func.__module__.split(".")[-1]
                
                cache_key = CacheKey.build(_namespace, key_parts)
            
            # Get Redis instance
            redis = CacheManager.get_instance()
            
            try:
                # Try to get from cache
                cached_value = redis.get(cache_key)
                if cached_value is not None:
                    return CacheSerializer.deserialize(cached_value)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result if not None or if cache_null is True
                if result is not None or _cache_null:
                    serialized = CacheSerializer.serialize(result)
                    redis.setex(cache_key, _expire, serialized)
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache error in {func.__name__}: {str(e)}")
                # On cache error, just execute the function
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return func(*args, **kwargs)
            
            # Check if caching should be skipped
            if skip_cache and skip_cache(*args, **kwargs):
                return func(*args, **kwargs)
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(func, *args, **kwargs)
            else:
                # Bind arguments to signature
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Build key parts
                key_parts = [
                    func.__module__,
                    func.__name__,
                    str(bound_args.arguments)
                ]
                
                # Use namespace from decorator or function's module
                _namespace = namespace or func.__module__.split(".")[-1]
                
                cache_key = CacheKey.build(_namespace, key_parts)
            
            # Get Redis instance
            redis = CacheManager.get_instance()
            
            try:
                # Try to get from cache
                cached_value = redis.get(cache_key)
                if cached_value is not None:
                    return CacheSerializer.deserialize(cached_value)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result if not None or if cache_null is True
                if result is not None or _cache_null:
                    serialized = CacheSerializer.serialize(result)
                    redis.setex(cache_key, _expire, serialized)
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache error in {func.__name__}: {str(e)}")
                # On cache error, just execute the function
                return func(*args, **kwargs)
        
        return async_wrapper if is_async else sync_wrapper
    
    return decorator

def invalidate_cache(
    namespace: Optional[str] = None,
    pattern: str = "*"
):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        namespace: Cache namespace to invalidate.
        pattern: Pattern of keys to invalidate.
    """
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            try:
                await clear_cache(pattern, namespace)
            except Exception as e:
                logger.warning(f"Cache invalidation error in {func.__name__}: {str(e)}")
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                asyncio.run(clear_cache(pattern, namespace))
            except Exception as e:
                logger.warning(f"Cache invalidation error in {func.__name__}: {str(e)}")
            return result
        
        return async_wrapper if is_async else sync_wrapper
    
    return decorator 