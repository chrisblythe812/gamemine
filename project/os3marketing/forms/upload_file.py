# -*- coding: utf-8 -*-
from django import forms
from project.os3marketing.core.export.csv_file import *
from project.os3marketing.core.export.vcard import *
from project.os3marketing.models import MailingList
from django.utils.translation import ugettext_lazy as _
class FormUpload(forms.Form):
    list = forms.ModelChoiceField(queryset=MailingList.objects.filter(type=MailingList.PRIVATE,behavior=MailingList.STATIC),empty_label=_(u"None"),required=False)
    file = forms.FileField()  
    def upload(self,source,type): 
        if type == 0: 
            return import_from_stream(source,self.cleaned_data['list'])  
        else:
            return vcard_contacts_import(source,self.cleaned_data['list'])  
            