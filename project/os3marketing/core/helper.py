# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.template.loader import render_to_string
from project.os3marketing import settings as os3settings
from project.os3marketing.core.libraries.BeautifulSoup import BeautifulSoup
from project.os3marketing.exception import ProfileDoesNotExist
from project.os3marketing.models import Link, Profile
from project.os3marketing.tokens import tokenize
import re
import urllib2



email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
    r')@(?:[A-Z0-9]+(?:-*[A-Z0-9]+)*\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain

def email_is_valid(email):
    return email_re.match(email)    


def body_insertion(content, insertion, end=False):
    """Insert an HTML content into the body HTML node"""
    if not content.startswith('<body'):
        content = '<body>%s</body>' % content
    soup = BeautifulSoup(content)

    if end:
        soup.body.append(insertion)
    else:
        soup.body.insert(0, insertion)
    return soup.prettify()

def render_string(template_string, context={}):
    """Shortcut for render a template string with a context"""
    t = Template(template_string)
    c = Context(context)
    return t.render(c)

def track_links(content, context):
    """Convert all links in the template for the user
    to track his navigation"""
    if not context.get('uidb36'):
        return content

    soup = BeautifulSoup(content)
    for link_markup in soup('a'):
        if link_markup.get('href'):
            link_href = link_markup['href']
            link_title = link_markup.get('title', link_href)
            link, created = Link.objects.get_or_create(url=link_href,
                                                       defaults={'title': link_title})
            link_markup['href'] = 'http://%s%s' % (context['domain'], reverse('os3marketing_clicked_link',
                                                                              args=[context['newsletter'].slug,
                                                                                    context['uidb36'], context['token'],
                                                                                    link.pk]))                
    return soup.prettify()


def get_unsubscription_url(newsletter,contact):
    """
    monta url de desinscricao
    """
    uidb36, token = tokenize(contact)   
    return render_string(os3settings.UNSUBSCRIPTION_URL,{'uidb36':uidb36,'token':token,'newsletter':newsletter})

def get_profile():
    try:
        return Profile.objects.all()[:1][0]
    except:
        raise ProfileDoesNotExist(u"Profile is no t configured.")

