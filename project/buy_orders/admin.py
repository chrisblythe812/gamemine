from logging import debug #@UnusedImport

from django.contrib import admin
from django.template import defaultfilters
from django.contrib.admin.util import unquote

from models import BuyOrder, BuyOrderItem


class BuyOrderItemInline(admin.StackedInline):
    model = BuyOrderItem
    extra = 0
    max_num = 0
    

class BuyOrdersAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'full_name', 'total', 'tax', 'order_total', 'applied_credits', 'charge_amount', 'status', 'date']
    list_filter = ['status', 'create_date']
    search_fields = ['id', 'create_date']
    fieldsets = (
        (None, {
            'fields': ['status'],
        }),
        ('Shipping Information', {
            'fields': ['first_name', 'last_name', 'shipping_address1', 'shipping_address2', 
                       'shipping_city', 'shipping_state', 'shipping_zip_code'],
        }),
        ('Billing Information', {
            'fields': ['billing_first_name', 'billing_last_name', 'billing_address1', 'billing_address2', 
                       'billing_city', 'billing_state', 'billing_zip_code'],
        }),
    )
#    inlines = [BuyOrderItemInline]

    def _format_address(self, data, prefix=None):
        k = ['address1', 'address2', 'city', 'state', 'zip']
        v = []
        for key in k:
            if prefix:
                key = '_'.join((prefix, key))
            if key in data and data[key]:
                v.append(data[key])
        return ', '.join(v)

    def order_no(self, obj):
        return '%08d' % obj.id

    def full_name(self, obj):
        return ' '.join([obj.first_name, obj.last_name])

    def shipping_address(self, obj):
        return self._format_address(obj.get_shipping_address_data())
    
    def card(self, obj):
        return obj.card_display_number
    
    def tracking_no(self, obj):
        return obj.tracking_number or ''
    
    def date(self, obj):
        return defaultfilters.date(obj.create_date)
    
    def order_total(self, obj):
        return obj.get_order_total()
    
    def charge_amount(self, obj):
        return obj.get_charge_amount()
    
    def change_view(self, request, object_id, extra_context=None):
#        model = self.model
#        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        extra_context = {
            'title': 'Order #%08d (%s)' % (obj.id, obj.get_status_display()),
        }
        return super(BuyOrdersAdmin, self).change_view(request, object_id, extra_context)
    
admin.site.register(BuyOrder, BuyOrdersAdmin)
