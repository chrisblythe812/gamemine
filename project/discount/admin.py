from django.contrib import admin

from models import CommonValues, CategoryDiscount, GenreDiscount, GroupDiscount, TagDiscount

class CommonValuesAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'value']
    list_editable = ['value']
    ordering = ['name']

class CategoryDiscountAdmin(admin.ModelAdmin):
    list_display = ['category', 'ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    list_editable = ['ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    ordering = ['category']

class GenreDiscountAdmin(admin.ModelAdmin):
    list_display = ['genre', 'ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    list_editable = ['ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    ordering = ['genre']

class TagDiscountAdmin(admin.ModelAdmin):
    list_display = ['tag', 'ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    list_editable = ['ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    ordering = ['tag']

class GroupDiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    list_editable = ['ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete', 'trade_price_complete', 'trade_credit']
    ordering = ['name']
    raw_id_fields = ("items",)

admin.site.register(CommonValues, CommonValuesAdmin)
admin.site.register(CategoryDiscount, CategoryDiscountAdmin)
admin.site.register(GenreDiscount, GenreDiscountAdmin)
admin.site.register(TagDiscount, TagDiscountAdmin)
admin.site.register(GroupDiscount, GroupDiscountAdmin)
