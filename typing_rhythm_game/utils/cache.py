from functools import wraps
from flask_caching import Cache
from flask import request, current_app

cache = Cache()

def cache_key_prefix():
    """Generate a cache key prefix based on the current user."""
    return f"user_{request.user_id}" if hasattr(request, 'user_id') else "anonymous"

def cached_with_user(timeout=300):
    """Cache decorator that includes user-specific information in the cache key."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{cache_key_prefix()}_{request.path}_{str(kwargs)}"
            return cache.get_or_set(
                cache_key,
                lambda: f(*args, **kwargs),
                timeout=timeout
            )
        return decorated_function
    return decorator

def invalidate_user_cache():
    """Invalidate all cache entries for the current user."""
    if not hasattr(request, 'user_id'):
        return
    
    pattern = f"{cache_key_prefix()}_*"
    cache.delete_pattern(pattern)
