from functools import wraps

from django.shortcuts import redirect


def redirect_if_authenticated(redirect_to, *the_args, **the_kwargs):
    def decorator(func):
        @wraps(func)
        def real_decorator(request, *args, **kwargs):
            if request.user.is_authenticated():
                return redirect(redirect_to, *the_args, **the_kwargs)
            else:
                return func(request, *args, **kwargs)
        return real_decorator
    return decorator
