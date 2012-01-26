from django.conf import settings

from project.catalog.models import Category


def common(request):
    return {
        'CATALOG_CATEGORIES': Category.list_names(),
        'DEFAULT_REVIEWS_COUNT': settings.DEFAULT_REVIEWS_COUNT,
    }
