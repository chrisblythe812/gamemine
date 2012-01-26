from django.core.cache import cache


def simple_cached_call(key, timeout=None):
    def decorator(func):
        def real_decorator(*args, **kwargs):
            v = cache.get(key)
            if not v:
                v = func(*args, **kwargs)
                cache.set(key, v, timeout)
            return v
        return real_decorator
    return decorator
