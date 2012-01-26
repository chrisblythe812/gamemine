# -*- coding: utf-8 -*-
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext,Template,Context
from django.template.loader import render_to_string as render_file
from project.os3marketing.core.helper import *
from project.os3marketing.models import Newsletter, ContactMailingStatus, Link, Profile
from project.os3marketing.settings import TRACKING_IMAGE
from project.os3marketing.tokens import untokenize
from project.os3marketing.forms.subscriptions import FormSubscriptions
from django.utils.translation import ugettext_lazy as _

import base64

def opened_on_site(request, slug, uidb36, token):
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    log = ContactMailingStatus.objects.create(newsletter=newsletter,
                                              contact=contact,
                                              status=ContactMailingStatus.OPENED_ON_SITE)
    profile = get_profile()
    unsubscription_url = get_unsubscription_url(newsletter,contact)    
    context = Context({'contact': contact,
               'uidb36': uidb36, 'token': token,
               'newsletter': newsletter,
               'domain': Site.objects.get_current().domain,
               'header_sender':newsletter.server.sender,
               'website':profile.website,
               'unsubscription_url':unsubscription_url})
       
    content = render_string(newsletter.content, context)
    content = track_links(content, context)
    try:
        unsubscription = Template(newsletter.cabecalho_rodape.rodape).render(context)
    except Exception,e:
        print e
        unsubscription = render_to_string('os3marketing/newsletter_link_unsubscribe.html', context)
    
    content = body_insertion(content, unsubscription, end=True)           
    return render_to_response('os3marketing/newsletter_detail.html',
                              {'content': content,
                               'object': newsletter},
                              context_instance=RequestContext(request))
    
    
def opened_email(request, slug, uidb36, token):
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    ContactMailingStatus.objects.create(newsletter=newsletter,
                                        contact=contact,
                                        status=ContactMailingStatus.OPENED)
    return HttpResponse(base64.b64decode(TRACKING_IMAGE), mimetype='image/png')
    
def clicked_link(request, slug, uidb36, token, link_id):
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    link = get_object_or_404(Link, pk=link_id)
    log = ContactMailingStatus.objects.create(newsletter=newsletter,
                                              contact=contact,
                                              status=ContactMailingStatus.LINK_OPENED,
                                              link=link)
    return HttpResponseRedirect(link.url)    

def mailinglist_unsubscribe(request, slug, uidb36, token):
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    profile = get_profile()
    msg = None
    if request.POST:
        form = FormSubscriptions(request.POST,contact=contact)
        if form.is_valid():
            form.update(newsletter)
            form = FormSubscriptions(contact=contact)
            msg = _('data has been successfully saved')
    else:
        form = FormSubscriptions(contact=contact)

    return render_to_response('os3marketing/unsubscribe.html',
                              Context({'form':form,'profile':profile,'msg':msg}),
                              context_instance=RequestContext(request))   