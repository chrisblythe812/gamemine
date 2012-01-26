# -*- coding: utf-8 -*-
"""ModelAdmin for MailingList"""
from datetime import datetime
from django import forms
from django.forms.models import ModelForm
from django.conf.urls.defaults import *
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from project.os3marketing.core.export.csv_file import export_csv_to_response
from project.os3marketing.core.export.vcard import \
    vcard_contacts_export_response
from project.os3marketing.models import MailingList, Newsletter, Filtering

class MailingListAdminForm(ModelForm):
    class Meta:
        model = MailingList
    def clean_behavior(self):
        if self.cleaned_data['behavior']:
            if self.cleaned_data['behavior'] == MailingList.DYNAMIC:
                if self.instance.pk:
                    if self.instance.subscribers.all().count() > 0:
                        raise forms.ValidationError("you can't have static subscribers into a dynamic mailing list. On Dynamic List the contacts should be get on fly.")
        return self.cleaned_data['behavior']

class FilteringInline(admin.TabularInline):
    model = Filtering
    extra = 3 
    
class MailingListAdmin(admin.ModelAdmin):
    form = MailingListAdminForm
    date_hierarchy = 'creation_date'
    list_display = ('name','behavior', 'get_type', 'creation_date','subscribers_count' ,'export_link','unsubscriber_historic_link') 
    list_filter = ('behavior','type','creation_date', 'modification_date')
    search_fields = ('name', 'description',)
    fieldsets = ((_('General data'), {'fields': ('behavior','name', 'description','type',)}),
                 )
    inlines = [FilteringInline]
    actions = ['merge_mailinglist']
    
    def save_formset(self, request, form, formset, change):
        super(MailingListAdmin,self).save_formset(request, form, formset, change)
        if change:
            if form.cleaned_data['behavior'] == MailingList.STATIC:
                form.instance.filtering_set.all().delete()
    
 
            
    def get_actions(self, request):
        actions = super(MailingListAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
        
    def get_type(self,obj):
        return obj.get_type_display()
    get_type.short_description = _('List Type')
    
    def merge_mailinglist(self, request, queryset):
        if queryset.filter(behavior=MailingList.DYNAMIC).count() > 0:
            messages.warning(request,_('you can not merge dynamic list.'))
            return None
                
        queryset = queryset.filter(type=MailingList.PRIVATE)
        if queryset.count() <= 1:
            messages.warning(request, _('Please choose at least two private lists.'))
            return None

        
        contacts = []
        for ml in queryset:
            for contact in ml.subscribers.all():
                contacts.append(contact)

        when = str(datetime.now()).split('.')[0]
        new_mailing = MailingList(name= u'%s %s' % (_(u'New list at'),when),
                                  description= u'%s %s' % (_(u'Created New list based on merging other at'),when),
                                  type=MailingList.PRIVATE,behavior=MailingList.STATIC)
        new_mailing.save()
        new_mailing.subscribers = set(contacts)

        self.message_user(request, u'%s %s'  % (new_mailing,_(u'Created successfully')) )
    merge_mailinglist.short_description = _(u'Merging private lists')

    def export_subscribers_to_vcard(self, request, mailinglist_id):
        mailinglist = get_object_or_404(MailingList, pk=mailinglist_id)
        name = u'%s_%s' % (_(u'contacts') , mailinglist.name)
        return vcard_contacts_export_response(mailinglist.contacts_set(), name)

    def export_subscribers_to_csv(self, request, mailinglist_id):
        mailinglist = get_object_or_404(MailingList, pk=mailinglist_id)
        name = u'%s_%s' % (_(u'contacts'),mailinglist.name)
        return export_csv_to_response(mailinglist.contacts_set(), name)

    def unsubscriber_historic(self,request,mailinglist_id):                  
        mailing = get_object_or_404(MailingList, id=mailinglist_id)
        opts = MailingList._meta
        context = {'title': _(u'Mailing List unsubscriptions') ,
                   'original': mailing,
                   'opts': opts,
                   'object_id': mailing.pk,
                   'app_label': opts.app_label,}
        return render_to_response('os3marketing/unsubscribers_historic.html',
                                  context, context_instance=RequestContext(request))
    
    def export_link(self, mailinglist):
        return '<a href="%s">VCARD</a> | <a href="%s">CSV</a>' % \
            (reverse('admin:mailinglist_export_to_vcard', args=[mailinglist.pk,]),
             reverse('admin:mailinglist_export_to_csv', args=[mailinglist.pk,]))
    
    export_link.allow_tags = True
    export_link.short_description = _(u'Export')
    
    def unsubscriber_historic_link(self,mailinglist):
        return u'<a href="%s">%s</a>' % ((reverse('admin:mailinglist_unsubscribers', args=[mailinglist.pk,])) , _(u'Visualizar'))
    
    unsubscriber_historic_link.allow_tags = True
    unsubscriber_historic_link.short_description = _(u'Unsubscriptions')    

     
    def get_urls(self):
        urls = super(MailingListAdmin, self).get_urls()
        my_urls = patterns('',
                       url(r'^export-vcard/(?P<mailinglist_id>\d+)/$', self.admin_site.admin_view(self.export_subscribers_to_vcard), name='mailinglist_export_to_vcard'),
                       url(r'^export-csv/(?P<mailinglist_id>\d+)/$', self.admin_site.admin_view(self.export_subscribers_to_csv), name='mailinglist_export_to_csv'),                       
                       url(r'^unsubscribers/(?P<mailinglist_id>\d+)/$', self.admin_site.admin_view(self.unsubscriber_historic), name='mailinglist_unsubscribers'),                       
                       )

        return my_urls + urls
    
    def delete_view(self, request, object_id, extra_context=None):
        ml = get_object_or_404(MailingList,pk=object_id)
        for n in ml.newsletter_set.all():
            if n.status not in [Newsletter.SENT,Newsletter.CANCELED]:
                messages.warning(request,_(u'A list can only be deleted  if the related newsletters are all in cancelled or sent status.'))
                return HttpResponseRedirect("../../")
        return super(MailingListAdmin,self).delete_view(request, object_id, extra_context)
    
    