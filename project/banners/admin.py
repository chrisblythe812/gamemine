from django.contrib import admin

from models import FeaturedGame

class FeaturedGameAdmin(admin.ModelAdmin):
    list_display = ['game', 'category', 'image', 'active']
    list_filter = ['category', 'active']
    search_fields = ['game__name']
    raw_id_fields = ['game']
    list_editable = ['active']

admin.site.register(FeaturedGame, FeaturedGameAdmin)
