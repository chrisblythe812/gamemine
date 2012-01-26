import logging
import sys
import datetime

from django.template.loader import get_template_from_string, get_template
from django.template import Context, TemplateDoesNotExist
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import send_mail, EmailMessage

from project.catalog.models.categories import Category


def mail(mailto, template, ctx={}, mailfrom=None, subject=None):
    mailfrom = mailfrom or settings.DEFAULT_FROM_EMAIL
    if isinstance(template, basestring): 
        ctx.update({
            'CATALOG_CATEGORIES': Category.list_names(),
            'SITE_URL': 'http://%s' % Site.objects.get_current().domain,
            'STATIC_URL': settings.EMAIL_STATIC_URL,
            'terms_url': 'http://www.gamemine.com/Terms/',
            'help_url': 'http://www.gamemine.com/Help-FAQs/',
            'WIMGW_url': 'http://www.gamemine.com/What-is-My-Game-Worth/',
        })
        try:
            body = get_template(template).render(Context(ctx))
            subject = subject or ''
        except TemplateDoesNotExist:
            template = Template.objects.get(name=template)
            subject = subject or get_template_from_string(u'{%% autoescape off %%}%s{%% endautoescape %%}' % template.subject).render(Context(ctx))
            body = get_template_from_string(u'{%% autoescape off %%}%s{%% endautoescape %%}' % template.body).render(Context(ctx))

    msg = EmailMessage(subject, body, mailfrom, [mailto])
    msg.content_subtype = "html"
    msg.send()
