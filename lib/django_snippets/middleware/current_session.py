from uuid import uuid4

from django.conf import settings


if hasattr(settings, 'FLASH_SESSION_COOKIE_NAME'):
    FLASH_SESSION_COOKIE_NAME = settings.FLASH_SESSION_COOKIE_NAME
else:
    FLASH_SESSION_COOKIE_NAME = 'XFlashSessionID'


class LazySessionId(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_current_session_id'):
            if FLASH_SESSION_COOKIE_NAME in request.COOKIES:
                request._cached_current_session_id = request.COOKIES[FLASH_SESSION_COOKIE_NAME]
            else:
                request._cached_current_session_id = str(uuid4()) 
        return request._cached_current_session_id


class CurrentSessionIDMiddleware(object):
    def process_request(self, request):
        request.__class__.current_session_id = LazySessionId()
        
    
    def process_response(self, request, response):
        if hasattr(request, '_cached_current_session_id'):
            response.set_cookie(FLASH_SESSION_COOKIE_NAME, request.current_session_id)
        return response
