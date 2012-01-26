# -*- coding: utf-8 -*-
"""ModelAdmin for Newsletter"""
from django.contrib import admin
from project.os3marketing.models import *
from project.os3marketing.widgets import CustomTinyMCEWidget
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
class TemplateAdminForm(ModelForm):
    class Meta:
        model = Template
    content = forms.CharField(label=(u"Newsletter"),widget=CustomTinyMCEWidget(attrs={'cols': 80, 'rows': 30}))

class TemplateAdmin(admin.ModelAdmin):
    form = TemplateAdminForm
    list_display = ('title',  )
    search_fields = ('title', 'content')
    save_on_top = True

