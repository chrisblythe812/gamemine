from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.template import Context
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from project.social_bookmarks.links import SOCIAL_BOOKMARKS_LINKS

register = template.Library()

LANGUAGE_CODE = str(getattr(settings, 'LANGUAGE_CODE', 'en'))
SOCIAL_BOOKMARKS_PERMALINK_FUNC = str(getattr(settings, 'SOCIAL_BOOKMARKS_PERMALINK_FUNC', 'get_absolute_url'))
SOCIAL_BOOKMARKS_OPEN_IN_NEW_WINDOW = bool(getattr(settings, 'SOCIAL_BOOKMARKS_OPEN_IN_NEW_WINDOW', True))
SOCIAL_BOOKMARKS = list(getattr(settings, 'SOCIAL_BOOKMARKS', []))

@register.inclusion_tag('social_bookmarks/social_bookmarks_links.html', takes_context=True)
def show_social_bookmarks(context, title, object_or_url, description=""):
    request = context['request']
    
    object = None
    if isinstance(object_or_url, (str, unicode)):
        url = object_or_url
    else:
        url = getattr(object_or_url, SOCIAL_BOOKMARKS_PERMALINK_FUNC)()
    
    url = urlquote(request.build_absolute_uri(url))
    title = urlquote(title)
    description = urlquote(description)
    
    page_dict = {
        'url': url,
        'title': title,
        'description': description,
        'language_code': LANGUAGE_CODE,
    }

    sites = []
    for key in SOCIAL_BOOKMARKS:
        s_name, s_title, s_href, s_image, js_opts = SOCIAL_BOOKMARKS_LINKS[key]
        if js_opts:
            s_js, s_onclick = js_opts
        else:
            s_js, s_onclick = None, None
        
        sites.append({
            'href': s_href % page_dict,
            'title': s_title,
            'image': s_image,
            'js': s_js,
            'onclick': s_onclick,
        })

    context.update({'social_bookmark_sites': sites, 'newwindow': SOCIAL_BOOKMARKS_OPEN_IN_NEW_WINDOW})
    return context
