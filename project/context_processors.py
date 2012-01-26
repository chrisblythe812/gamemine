from operator import and_

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.messages.api import get_messages


def core(request):
    # If all messages have "link-dialog" tag then adding ``all_hidden``
    # attribute
    messages = get_messages(request)
    if messages:
        messages.all_hidden = reduce(and_, ["link-dialog" in m.tags for m in messages])

    return {
        "REV": settings.REV,
        "SITE_URL": "http://%s" % Site.objects.get_current().domain,
        "campaign_cid": request.campaign_id,
        "campaign_sid": request.sid,
        "affiliate": request.affiliate,
        "messages": messages,
    }
