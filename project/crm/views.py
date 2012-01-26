from logging import debug, error #@UnusedImport
from datetime import datetime

from django.http import HttpResponseBadRequest, HttpResponse
from django.conf import settings
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt

from project.crm.models import FeedbackifyFeedback


@csrf_exempt
def ifn(request):
    debug('Got request from feedbackify!')
    if request.method != 'POST':
        return HttpResponseBadRequest()
    key = request.POST.get('key') 
    if key != settings.FEEDBACKIFY_IFN_KEY:
        return HttpResponseBadRequest()
    try:
        payload = simplejson.loads(request.POST['payload'])
        debug(payload)
        FeedbackifyFeedback(
            timestamp=datetime.fromtimestamp(payload['timestamp']),
            form_id=payload['formId'],
            item_id=payload['itemId'],
            score=payload['score'],
            category=payload['category'],
            subcategory=payload['subcategory'],
            feedback=payload['feedback'],
            email=payload['email'],
            context=payload['context'],
            payload=payload,
        ).save()
    except Exception, e:
        error(e)
        return HttpResponseBadRequest()
    return HttpResponse('OK')
