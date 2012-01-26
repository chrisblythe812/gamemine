from django.contrib import admin

from project.trade.models import TradeOrderItem, TradeOrder


class TradeOrderItemAdmin(admin.TabularInline):
    model = TradeOrderItem
    extra = 0
    can_delete = False

class TradeOrderAdmin(admin.ModelAdmin):
    list_display = ('order_no', 'get_received_date', 'get_fullname',)
    inlines = [TradeOrderItemAdmin]
    
    def has_add_permission(self, *args, **kwargs):
        return False

#    def has_delete_permission(self, *args, **kwargs):
#        return False

admin.site.register(TradeOrder, TradeOrderAdmin)

