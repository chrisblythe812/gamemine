from functools import wraps

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext


def simple_view(template, mimetype="text/html", cookies=None):
    """
    Simplify views declararation.

    Usage:

    @simple_view("path/to/template.html")
    def view1(request):
        ...
        return {
            "context_var1": context_var1,
        }

    @simple_view("path/to/template.txt", mimetype="text/plain")
    def view2(request):
        pass # it"s ok to return nothing

    @simple_view("path/to/template.html")
    def view3(request):
        if some_condition:
            return redirect("view1") # You could return HttpResponse object
        return {}
    """
    def decorator(func):
        @wraps(func)
        def real_decorator(request, *args, **kwargs):
            returned = func(request, *args, **kwargs)
            if isinstance(returned, HttpResponse):
                return returned
            assert returned is None or isinstance(returned, dict)
            response = render_to_response(template,
                                          returned or {},
                                          context_instance=RequestContext(request))
            for cookie in cookies or []:
                response.set_cookie(**cookie)
            return response
        return real_decorator
    return decorator
