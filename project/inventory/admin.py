from django.contrib import admin

from project.inventory.models import Distributor, Dropship, Purchase,\
    Inventory


class DistributorAdmin(admin.ModelAdmin):
    list_display = ['name', 'address']
    search_fields = ['name', 'address']


class DropshipAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code', 'address', 'city', 'state', 'postal_code', 'bid']
    list_display = ['name', 'code', 'address', 'city', 'state', 'postal_code', 'bid']


class PurchaseAdmin(admin.ModelAdmin):
    search_fields = ['created']
    list_display = ['created', 'status', 'distributor', 'is_new']
    list_filter = ['created', 'status', 'distributor', 'is_new']


class InventoryAdmin(admin.ModelAdmin):
    search_fields = ['item__name', 'barcode', 'item__id', 'item__upc']
    list_display = ['item', 'upc', 'category', 'dropship', 'barcode', 'is_new', 'status', 'manual_checked']
    list_filter = ['dropship', 'is_new', 'status', 'manual_checked']
    fieldsets = (
        (None, {
            'fields': ('dropship', 'barcode', 'is_new', 'status', 'buy_only', ),
        }),
    )

    def category(self, obj):
        return obj.item.category
    
    def upc(self, obj):
        return obj.item.upc
    upc.short_description = 'UPC'


#class DistributorItemAdmin(admin.ModelAdmin):
#    list_display = ['created', 'status', 'distributor', 'is_new']


admin.site.register(Distributor, DistributorAdmin)
admin.site.register(Dropship, DropshipAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Inventory, InventoryAdmin)
#admin.site.register(DistributorItem, DistributorItemAdmin)
