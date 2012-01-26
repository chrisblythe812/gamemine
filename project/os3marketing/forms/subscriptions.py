# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import get_object_or_404
from project.os3marketing.models import MailingList, Contact, ContactMailingStatus
from project.os3marketing.widgets import CustomCheckboxSelectMultiple, \
    HorizRadioRenderer
from django.utils.translation import ugettext_lazy as _

class FormSubscriptions(forms.Form):
    list = forms.ModelMultipleChoiceField(queryset=MailingList.objects.none(),required=False,
                                          widget=CustomCheckboxSelectMultiple(div_style='width:400px;',li_style='width:50%;'))    
  
    subscription = forms.ChoiceField(choices=[(0,_(u'Yes')),(2,_(u'No'))],widget=forms.RadioSelect(renderer=HorizRadioRenderer))    
    
    def __init__(self, *args, **kwargs):
        if 'contact' in kwargs:
            self.contact = kwargs['contact']
            del kwargs['contact']
        super(FormSubscriptions, self).__init__(*args, **kwargs)    
        self.fields['list'].queryset = MailingList.objects.filter(type=MailingList.PUBLIC)
        if self.contact:
            self.current_mailinglists_subscriber = self.contact.mailinglist_subscriber.filter(type=MailingList.PUBLIC)
            self.current_mailinglists_unsubscriber = self.contact.mailinglist_unsubscriber.filter(type=MailingList.PUBLIC)                       
            self.initial['list'] = self.current_mailinglists_subscriber.exclude(id__in=self.current_mailinglists_unsubscriber.values_list('id').query).values_list('id',flat=True)
            self.initial['subscription'] = self.contact.status

    def update(self,newsletter=None):    
        lists = self.cleaned_data['list']
        self.contact.status = self.cleaned_data['subscription'] 
        self.contact.save()
        for l in self.current_mailinglists_subscriber:
            if l in lists:
                if l in self.current_mailinglists_unsubscriber:
                    l.unsubscribers.remove(self.contact)                  
            else:
                l.unsubscribers.add(self.contact)
                if newsletter:
                    if l in newsletter.mailing_list.all():
                        ContactMailingStatus.objects.get_or_create(newsletter=newsletter, contact=self.contact,
                                                            status=ContactMailingStatus.UNSUBSCRIPTION) 
        for l in lists:
            if l not in self.current_mailinglists_subscriber:
                l.subscribers.add(self.contact)
            
        