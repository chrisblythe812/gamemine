# -*- coding: utf-8 -*-
"""ModelAdmin for SMTPServer"""
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class SMTPServerAdmin(admin.ModelAdmin):
    list_display = ('alias', 'server', 'port', 'user', 'tls', 'mails_hour','sender','reply_to')
    list_filter = ('tls',)
    search_fields = ('alias', 'server', 'user',)
    fieldsets = ((None, {'fields': ('alias','active'),}),
                 (_(u'Configurations'), {'fields': ('server', 'port',
                                                'user', 'password', 'tls'),}),
                 (_(u'Miscellaneous'), {'fields' : ('sender','reply_to','mails_hour'),}),
                 )
    actions = ['check_connections']


    def check_connections(self, request, queryset):
        message = '%s - %s'
        for server in queryset:
            if server.check_connection():
                status = u"%s" % _(u'connected successfully') 
            else:
                status = "%s" % _(u'impossible to connect.')
            self.message_user(request, message % (server, status))
    check_connections.short_description = _(u'Test connection')