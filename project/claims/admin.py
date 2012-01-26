from django.contrib import admin
from project.claims.models import Claim


class ClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_object', 'email', 'date', 'sphere_of_claim', 'type', 'status']
    list_filter = ['status', 'type', 'sphere_of_claim', 'date']
    search_fields = ['user__email', 'object_id']
#    raw_id_fields = ['inventory', 'item']
#    fieldsets = (
#        (None, {
#            'fields': ('status', 'date_shipped', ),
#        }),
#    )
#
    def email(self, obj):
        return obj.user.email

admin.site.register(Claim, ClaimAdmin)
