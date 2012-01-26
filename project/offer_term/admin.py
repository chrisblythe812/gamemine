# -*- coding: utf-8 -*-
from django.contrib import admin
from models import OfferTerm

class OfferTermAdmin(admin.ModelAdmin):
    list_display = ('id', 'type')
    
admin.site.register(OfferTerm,OfferTermAdmin)    

