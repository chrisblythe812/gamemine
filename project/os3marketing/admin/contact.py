# -*- coding: utf-8 -*-
"""ModelAdmin for Contact"""
from datetime import datetime
from django.conf.urls.defaults import *
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from project.os3marketing.core.export.csv_file import *
from project.os3marketing.core.export.vcard import *
from project.os3marketing.models import MailingList, Contact
from django import forms
from project.os3marketing.forms.upload_file import FormUpload
from django.utils.translation import ugettext_lazy as _
from project.os3marketing.helper import monta_query_string
from project.members.models import *    
from project.rent.models import *   
from django.db.models import Q

class SimpleMailingListForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput,required=False)
    mailingList = forms.ModelChoiceField(label=u'Choose a mailing list:',queryset=MailingList.objects.filter(type=MailingList.PRIVATE,behavior=MailingList.STATIC),required=False)

class MailingListForm(SimpleMailingListForm):
    newList = forms.CharField(label="or create a new one:",required=False)

class ContactAdminForm(forms.ModelForm):
    mailing_list = forms.ModelMultipleChoiceField(label=_(u"mailing list"),queryset=MailingList.objects.none(),required=False)
    class Meta:
        model = Contact
 
    def __init__(self, *args, **kwargs):
        super(ContactAdminForm, self).__init__(*args, **kwargs)
        self.fields['mailing_list'].queryset = MailingList.objects.all()         
        if kwargs.has_key('instance'):
            self.initial['mailing_list'] = kwargs['instance'].mailinglist_subscriber.all().values_list('id',flat=True)
                  

class ContactAdmin(admin.ModelAdmin):
    form = ContactAdminForm
    list_display = ('email', 'first_name', 'last_name', 'tester', 'get_status',
                    'total_subscriptions', 'creation_date')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
                    (_(u'Personal information'), {'fields': ('email', 'first_name', 'last_name',)}),
                    (_(u'Details'), {'fields': ('status','tester',)}),
                    (_(u'Lists'), {'fields': ('mailing_list',)}),                    
                 )
    actions = ['export_select_vcard','export_selected_csv','create_mailinglist' ,] 
    
    def save_model(self, request, obj, form, change):
        obj.save()
        obj.mailinglist_subscriber.clear()
        for m in form.cleaned_data['mailing_list']:            
            m.subscribers.add(obj)             
  
    def get_status(self,obj):
        return obj.get_status_display()
    get_status.short_description = _(u'Status')
    
    def total_subscriptions(self, contact):
        subscriptions = contact.subscriptions().count()
        unsubscriptions = contact.unsubscriptions().count()
        return '%s / %s' % (subscriptions - unsubscriptions, subscriptions)
    total_subscriptions.short_description = _(u'# of subscribers')

    def export_select_vcard(self, request, queryset):
        return vcard_contacts_export_response(queryset)
    export_select_vcard.short_description = _(u"Export contact(s) as VCARD")

    def export_selected_csv(self, request, queryset):
        return export_csv_to_response(queryset)
    export_selected_csv.short_description = _(u"Export contact(s) as CSV")  
    

    def create_mailinglist(self, request, queryset):
        when = str(datetime.now()).split('.')[0]
        new_mailing = MailingList(name=u'%s %s' % (_(u'New List at'),when),
                                  description=u'',
                                  type=MailingList.PRIVATE,behavior=MailingList.STATIC)
        new_mailing.save()
        new_mailing.subscribers = queryset
        self.message_user(request, u'%s %s' % (new_mailing , _(u'New list in')))
    create_mailinglist.short_description = _(u'Create a list based on the selected contacts')

    def import_vcard(self, request):
        opts = self.model._meta

        if request.POST:
            form = FormUpload(request.POST,request.FILES)
            if form.is_valid():
                source = request.FILES['file']     
                inserted = form.upload(source,1)
                if inserted == 0:
                    self.message_user(request, _(u'No contact imported'))
                else:
                    self.message_user(request, u'%s %s' % (inserted, _(u'Contacts imported successfully.')) )  
                    return HttpResponseRedirect("../../")          
        else:
            form = FormUpload()
        context = {'title': _(u'Contact import'),
                   'opts': opts,
                   'root_path': self.admin_site.root_path,
                   'app_label': opts.app_label,
                   'form':form}

        return render_to_response('os3marketing/contact_import_vcard.html',
                                  context, RequestContext(request))
    

    def import_csv(self, request):
        opts = self.model._meta
        if request.POST:
            form = FormUpload(request.POST,request.FILES)
            if form.is_valid():
                source = request.FILES['file']             
                inserted = form.upload(source,0)
                if inserted == 0:
                    self.message_user(request, _(u'No contact imported'))
                else:
                    self.message_user(request, u'%s %s' % (inserted , _(u'Contacts imported successfully.')) )  
                    return HttpResponseRedirect("../../")          
        else:
            form = FormUpload()

            
        context = {'title': _(u'Contact Import'),
                   'opts': opts,
                   'root_path': self.admin_site.root_path,
                   'app_label': opts.app_label,
                   'form':form}

        return render_to_response('os3marketing/contact_import_csv.html',
                                  context, RequestContext(request))        

    def export_vcard(self, request):
        return vcard_contacts_export_response(Contact.objects.all(),_(u'all_contacts'))

    def export_csv(self, request):
        return export_csv_to_response(Contact.objects.all(),_(u'all_contacts'))
#    
    def get_urls(self):
        urls = super(ContactAdmin, self).get_urls()
        my_urls = patterns('',
                           url(r'^import-vcard/$', self.admin_site.admin_view(self.import_vcard),
                               name='os3marketing_contact_import_vcard'),
                           url(r'^import-csv/$', self.admin_site.admin_view(self.import_csv),
                               name='os3marketing_contact_import_csv'),                               
                           url(r'^export-vcard/$', self.admin_site.admin_view(self.export_vcard),
                               name='os3marketing_contact_export_vcard'),
                           url(r'^export-csv/$', self.admin_site.admin_view(self.export_csv),
                               name='os3marketing_contact_export_csv'),)        
        return my_urls + urls
   
    def queryset(self, request):
        qs = super(ContactAdmin, self).queryset(request)
        profile = Profile.objects.all()
        if request.POST and not (request.POST.has_key('action') or request.POST.has_key('_save')):
            if int(request.POST['entry_point']) <> -1:
                profile = profile.filter(entry_point=request.POST['entry_point'])
            if int(request.POST['rent_status']) <> -1:
                profile = profile.filter(user__pk__in=MemberRentalPlan.objects.filter(status=request.POST['rent_status']).values('user').order_by('user').query)                
            if int(request.POST['member_only']) <> -1:
                profile = profile.filter(user__is_staff=int(request.POST['member_only']))
            if int(request.POST['profile_status']) <> -1:
                profile = profile.filter(account_status=request.POST['profile_status'])           
            if int(request.POST['contact_status']) <> -1:
                qs = qs.filter(status=int(request.POST['contact_status'])) 
            if int(request.POST['test_contact']) <> -1:
                qs = qs.filter(tester=int(request.POST['test_contact'])) 
            if int(request.POST['mail_list']) <> -1:
                qs = qs.filter(mailinglist_subscriber__id=int(request.POST['mail_list']))                                 
            
            if int(request.POST['entry_point']) <> -1 or int(request.POST['rent_status']) <> -1 or int(request.POST['member_only']) <> -1 or \
                int(request.POST['profile_status']) <> -1:   
                profile = profile.values('user__email').query            
                qs = qs.filter(email__in=profile)            
            if request.POST.has_key('q'):
                q = request.POST['q']
                qs = qs.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
                
        return qs    
  
    def create_filter_queryset(self,request,queryset):
        tuple = ()
        for s in queryset:
            tuple += ((s.pk,s),)
        return self.create_filter(request, tuple)
    
    def create_filter(self,request,query):
        
        list = []
        list.append( (-1,'All') )
        for s in query:
            list.append(s)
        
        return list    
        
    def changelist_view(self, request, extra_context=None):
        extra_context = {}
        """filters"""       
        extra_context['entry_point_list'] = self.create_filter(request, ENTRY_POINTS)
        extra_context['rent_status_list'] = self.create_filter(request, RENTAL_PLAN_STATUS)        
        extra_context['member_only_list'] = self.create_filter(request, ((1,'Yes'),(0,'No')))        
        extra_context['profile_status_list'] = self.create_filter(request, ACCOUNT_STATUSES)
        extra_context['contact_status_list'] = self.create_filter(request, Contact.STATUS_CHOICES)
        extra_context['test_contact_list'] = self.create_filter(request, ((1,'Yes'),(0,'No')))
        extra_context['mailinglist_list'] = self.create_filter_queryset(request, MailingList.objects.filter(type=MailingList.PRIVATE,behavior=MailingList.STATIC).order_by('name'))
        
        extra_context['current_entry_point'] = int(request.POST.get('entry_point',-1))
        extra_context['current_rent_status'] = int(request.POST.get('rent_status',-1))
        extra_context['current_member_only'] = int(request.POST.get('member_only',-1))
        extra_context['current_profile_status'] = int(request.POST.get('profile_status',-1))
        extra_context['current_contact_status'] = int(request.POST.get('contact_status',-1))
        extra_context['current_test_contact'] = int(request.POST.get('test_contact',-1))
        extra_context['current_mail'] = int(request.POST.get('mail_list',-1))        
        extra_context['q'] = request.POST.get('q','')
       
        if request.POST and not request.POST.has_key('action') and (request.POST.has_key('update') or request.POST.has_key('remove')):
            form = MailingListForm(request.POST)
            if form.is_valid():
                try:
                    ChangeList = self.get_changelist(request)
                    cl = ChangeList(request, self.model, self.list_display, self.list_display_links, self.list_filter,
                        self.date_hierarchy, self.search_fields, self.list_select_related, self.list_per_page, self.list_editable, self)
                    mailingList = form.cleaned_data['mailingList']
                    if mailingList is None:                    
                        mailingList = MailingList(name=form.cleaned_data['newList'] ,
                                      description=u'',
                                      type=MailingList.PRIVATE,behavior=MailingList.STATIC)
                        mailingList.save()

                    for c in cl.get_query_set():
                        if request.POST.has_key('remove'):
                            mailingList.subscribers.remove(c)  
                        else:
                            mailingList.subscribers.add(c)  
                    if request.POST.has_key('remove') and form.cleaned_data['mailingList']: 
                        self.message_user(request, u'Removed contacts from %s' % mailingList)
                    else:
                        self.message_user(request, u'Added contacts to %s' % mailingList)
                
                except: 
                    pass
        else:
            form = MailingListForm()
            
        extra_context['mailing_form'] = form
        return super(ContactAdmin,self).changelist_view(request,extra_context)                    
           