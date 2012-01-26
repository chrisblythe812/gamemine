from django.contrib import comments
from django.template import RequestContext
from django.template.loader import render_to_string

from project.catalog.models import Item


def get_template_list(model, suffix=''):
    if suffix:
        suffix = '.' + suffix
    return [
        "comments/%s_%s_preview%s.html" % (model._meta.app_label, model._meta.module_name, suffix),
        "comments/%s_preview%s.html" % (model._meta.app_label, suffix),
        "comments/%s/%s/preview%s.html" % (model._meta.app_label, model._meta.module_name, suffix),
        "comments/%s/preview%s.html" % (model._meta.app_label, suffix),
        "comments/preview%s.html" % suffix,
    ]

def render_review_form(request, target):
    form = comments.get_form()(target)
    context = {
        "comment" : form.data.get("comment", ""),
        "form" : form,
        "item": target,
    }
    request_context = RequestContext(request, {})
    return render_to_string(get_template_list(Item, 'form'), 
                            context, 
                            request_context)
