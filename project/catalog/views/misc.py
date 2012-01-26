from logging import debug #@UnusedImport

from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from django.conf import settings

from django_snippets.views import JsonResponse, simple_view

from project.catalog.models import Publisher, Category, Item
from project.catalog.views import get_item_json_synopsis


def ajax_required(redirect_to):
    def decorator_wrapper(func):
        def decorator(request, *args, **kwargs):
            if not settings.DEBUG and not request.is_ajax():
                return redirect(redirect_to)
            res = func(request, *args, **kwargs)
            if isinstance(res, HttpResponse):
                return res
            return JsonResponse(res)
        return decorator
    return decorator_wrapper


@ajax_required('catalog:index')
def popular_by_publisher(request, id):
    publisher = get_object_or_404(Publisher, pk=id)
    return {
        'items': [get_item_json_synopsis(item) for item in Item.list_popular_by_publisher(publisher, 12)], 
    }


@ajax_required('catalog:index')
def popular_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return {
        'items': [get_item_json_synopsis(item) for item in Item.list_popular_by_category(category, 12)], 
    }

@simple_view('catalog/esrb.html')
def esrb(request):
    return {}
