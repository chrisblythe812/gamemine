# -*- coding: utf-8 -*-
"""ModelAdmin for Newsletter"""
from django.contrib import admin
from project.os3marketing.models import *
from project.os3marketing.widgets import CustomTinyMCEWidget
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

class CabecalhoRodapeAdminForm(ModelForm):
    class Meta:
        model = CabecalhoRodape
    cabecalho = forms.CharField(label=_(u'Header'),widget=forms.Textarea(attrs={'style':'width:900px;height:300px;'}))    
    rodape = forms.CharField(label=_(u'Footer'),widget=forms.Textarea(attrs={'style':'width:900px;height:300px;'}))    

class CabecalhoAdmin(admin.ModelAdmin):
    form = CabecalhoRodapeAdminForm
    list_display = ('id', 'padrao', 'cabecalho' )

