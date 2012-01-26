from django.contrib import admin
from project.taxes.models import County, ByCountyTax, ByStateTax


class CountyAdmin(admin.ModelAdmin):
    list_display = ['state', 'name']
    ordering = ['state', 'name']
    list_filter = ['state']
    search_fields = ['state', 'name']

class ByCountyTaxAdmin(admin.ModelAdmin):
    list_display = ['county', 'state', 'value']
    search_fields = ['county__state', 'county__name']
    
    def state(self, obj):
        return obj.county.state

class ByStateTaxAdmin(admin.ModelAdmin):
    list_display = ['state', 'value']
    list_filter = ['state']

admin.site.register(County, CountyAdmin)
admin.site.register(ByCountyTax, ByCountyTaxAdmin)
admin.site.register(ByStateTax, ByStateTaxAdmin)
