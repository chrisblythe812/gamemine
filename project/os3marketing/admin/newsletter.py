# -*- coding: utf-8 -*-
"""ModelAdmin for Newsletter"""
from HTMLParser import HTMLParseError
from django import forms
from django.conf.urls.defaults import *
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import models
from django.forms.models import ModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from project.os3marketing.mailer import Mailer
from project.os3marketing.models import *
from project.os3marketing.statistics import get_statistics
from project.os3marketing.widgets import TemplateButtonMCEWidget
from django.utils.translation import ugettext_lazy as _

import json

class NewsletterAdminForm(ModelForm):
    class Meta:
        model = Newsletter
    content = forms.CharField(label=_("Newsletter"),widget=TemplateButtonMCEWidget(attrs={'cols': 80, 'rows': 30}))
    def __init__(self, *args, **kwargs): 
        super(NewsletterAdminForm,self).__init__(*args, **kwargs)
        try:
            if self.instance.pk:
                self.fields['server'].queryset = SMTPServer.objects.filter(models.Q(pk=self.instance.server.pk)|models.Q(pk=self.instance.server.pk))
            else:
                self.fields['server'].queryset = SMTPServer.objects.active()
                self.fields['server'].initial = SMTPServer.objects.active().order_by('id')[:1][0].pk 
                self.fields['cabecalho_rodape'].initial = CabecalhoRodape.objects.get(padrao=True).pk
        except:
            pass     

class NewsletterAdmin(admin.ModelAdmin):  
    form = NewsletterAdminForm
    date_hierarchy = 'creation_date'
    list_display = ('title', 'server', 'get_colored_status','sending_date','get_total_contacts','statistics_link','historic_link' )
    list_filter = ('creation_date',)
    search_fields = ('title', 'content')
    filter_horizontal = ['mailing_list']
    fieldsets = ((_(u'General Data'), {'fields': ('title', 'content',)}),
                 (_(u'List'), {'fields': ('mailing_list', )}),
                 (_(u'Miscellaneous'), {'fields': ('server','cabecalho_rodape',),
                                 'classes': ('collapse',)}),
                 )
    
    actions = ['send_mail_test', 'make_ready_to_send', 'make_cancel_sending']
    save_on_top = True

    def get_total_contacts(self,obj):
        return obj.total_subscribers()
    get_total_contacts.short_description = 'Total contacts'       
     
    def get_colored_status(self,obj):
        s = "<div style='color: #ffffff; font-weight:bold; padding: 3px; background:%s'>"+obj.get_status_display()+"</div>" 
        if obj.status == Newsletter.DRAFT :
            return s % "#e9e9e9;";
        elif obj.status == Newsletter.WAITING :
            return s % "#07ccf0;";
        elif obj.status == Newsletter.CANCELED :
            return s % "red;";
        elif obj.status == Newsletter.SENDING :
            return s % "#a9c47d;";
        else:                                
            return s % "green;";    
    get_colored_status.short_description = _("Status")
    get_colored_status.allow_tags = True  

    def newsletter_statistics(self,request, id):
        opts = Newsletter._meta
        newsletter = get_object_or_404(Newsletter, pk=id)
    
        context = {'title': u'%s %s' % (_(u'Statistics:') , newsletter),
                   'object': newsletter,
                   'opts': opts,
                   'object_id': newsletter.pk,
                   'app_label': opts.app_label,
                   'stats': get_statistics(newsletter)}
    
        return render_to_response('os3marketing/newsletter_statistics.html',
                                  context, context_instance=RequestContext(request))

#
    def statistics_link(self, newsletter):
        return u'<a href="%s">%s</a>' % (reverse('admin:newsletter_statistics', args=[newsletter.pk,]), _(u'View'))
    statistics_link.allow_tags = True
    statistics_link.short_description = _(u'Statistic')

    def newsletter_historic(self,request, id):
        """Exibe historico de envio"""
        opts = Newsletter._meta
        newsletter = get_object_or_404(Newsletter, pk=id)
        
        context = {'title': u'%s %s' % (_(u'History:'),newsletter),
                   'original': newsletter,
                   'opts': opts,
                   'object_id': newsletter.pk,
                   'app_label': opts.app_label,}
        return render_to_response('os3marketing/newsletter_historic.html',
                                  context, context_instance=RequestContext(request))
        
    def historic_link(self, newsletter):
        return u'<a href="%s">%s</a>' % (reverse('admin:newsletter_historic', args=[newsletter.pk,]), _(u'View'))
    historic_link.allow_tags = True
    historic_link.short_description = _(u'History')

    def send_mail_test(self, request, queryset):
        if Contact.objects.testers():
            for newsletter in queryset:
                mailer = Mailer(newsletter, test=True)
                try:
                    mailer.run()
                except HTMLParseError:
                    self.message_user(request, _(u'newsletter send failed, HTML has errors.'))
                    continue
                self.message_user(request, _(u'test sent successfully'))
        else:
            self.message_user(request, _(u'There are no test contacts registered.' ))
    send_mail_test.short_description = _(u'Send test email')
#
    def make_ready_to_send(self, request, queryset):
        queryset = queryset.filter(status=Newsletter.DRAFT)
        for newsletter in queryset:
            newsletter.status = Newsletter.WAITING
            newsletter.save()
        self.message_user(request, u'%s %s'  % (queryset.count() , _(u'newsletters ready to be sent')) )
    make_ready_to_send.short_description = _(u'Mark as ready to be sent')

    def make_cancel_sending(self, request, queryset):
        queryset = queryset.filter(models.Q(status=Newsletter.WAITING) |
                                   models.Q(status=Newsletter.SENDING))
        
        for newsletter in queryset:
            newsletter.status = Newsletter.CANCELED
            newsletter.save()
        self.message_user(request, u'%s %s' % (queryset.count() , _(u'newsletters cancelled')))
    make_cancel_sending.short_description = _(u'Cancel send')

    def template_options(self,request):
        templates = Template.objects.all()
        return render_to_response('os3marketing/template_options.html',
                                  locals(), context_instance=RequestContext(request))
      
    def load_template(self,request):
        template = Template.objects.get(pk=request.GET['template'])
        data = {'content':template.content}
        return HttpResponse(json.dumps(data), mimetype="application/json")      
     
    def get_urls(self):
        urls = super(NewsletterAdmin, self).get_urls()
        my_urls = patterns('',
                       url(r'^statistic/(?P<id>\d+)$', self.admin_site.admin_view(self.newsletter_statistics), name='newsletter_statistics'),        
                       url(r'^historic/(?P<id>\d+)$', self.admin_site.admin_view(self.newsletter_historic), name='newsletter_historic'),                                             
                       url(r'^load-template-options$', self.admin_site.admin_view(self.template_options), name='load_template_options'),                       
                       url(r'^load-template$', self.admin_site.admin_view(self.load_template), name='load_template'),                       

                  )
        return my_urls + urls
