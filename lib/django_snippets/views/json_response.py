from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils import simplejson
from django.conf import settings


class JsonResponse(HttpResponse):
    def __init__(self, object):
        if isinstance(object, QuerySet):
            content = serialize('json', object)
        else:
            content = simplejson.dumps(object, indent=2 if settings.DEBUG else None)
        super(JsonResponse, self).__init__(
            content, content_type='application/json')
