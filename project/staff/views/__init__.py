from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseBadRequest


staff_only = user_passes_test(lambda x: x.is_staff, login_url='/Member-Home/Login/')
superuser_required = user_passes_test(lambda x: x.is_superuser, login_url='/Member-Home/Login/')

def ajax_only(func):
    def decorator(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return func(request, *args, **kwargs)
    return decorator
