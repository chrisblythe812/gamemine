from django.conf.urls.defaults import * #@UnusedWildImport
from django.contrib import admin

from models import * #@UnusedWildImport


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'slug', 'type', 'active', 'ordering']
    list_filter = ['type', 'active']
    search_fields = ['name', 'description', 'slug']
    list_editable = ['ordering']


class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'ordering', 'type']
    list_filter = ['type']
    search_fields = ['name', 'description']
    list_editable = ['ordering']


class ItemAdmin(admin.ModelAdmin):
    list_display = ['upc', 'short_name', 'category', 'type', 'publisher', 'release_date',
                    'active', 'N', 'U', 'T', 'R', 'n_price', 'u_price', 't_price', 'rent_status']
    list_filter = ['rent_status', 'active', 'category', 'type', 'genres', 'release_date']
#    list_editable = ['sold_amount', 'trade_amount', 'rent_amount']
    search_fields = ['id', 'name', 'short_name', 'upc', 'slug']

    def N(self, obj):
        return obj.available_for_selling_n() or ''

    def U(self, obj):
        return obj.available_for_selling_u() or ''

    def T(self, obj):
        return 'X' if obj.trade_flag else ''

    def R(self, obj):
        return 'X' if obj.rent_flag else ''

    def n_price(self, obj):
        return obj.retail_price_new or ''

    def u_price(self, obj):
        return obj.retail_price_used or ''

    def t_price(self, obj):
        return obj.trade_price or ''

#    def get_urls(self):
#        return patterns('',
#            (r'^upload/$', self.admin_site.admin_view(self.upload_master_product_list)),
#            (r'^upload/handle/$', self.admin_site.admin_view(self.handle_uploaded_file)),
#        ) + super(ItemAdmin, self).get_urls()
#
#    def upload_master_product_list(self, request):
#        context = {
#            'title': 'Upload Master Product List',
#            'current_app': self.admin_site.name,
#            'opts': self.model._meta,
#        }
#        return render_to_response('catalog/admin/upload_master_product_list.html',
#                                  context, context_instance=RequestContext(request))
#
#    def handle_uploaded_file(self, request):
#        context = {
#            'title': 'Upload Master Product List',
#            'current_app': self.admin_site.name,
#            'opts': self.model._meta,
#        }
#        return render_to_response('catalog/admin/upload_master_product_list.html',
#                                  context, context_instance=RequestContext(request))


class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'url']
    list_filter = ['type']
    search_fields = ['name', 'description', 'url']
    ordering = ['name']


class RatingAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'type', 'esrb_symbol']
    list_filter = ['type']
    search_fields = ['title', 'description']


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['date', 'user_email', 'synopsis', 'rating', 'ip_address', 'content_object']
    list_filter = ['timestamp', 'rating']
    search_fields = ['user__username', 'user__email', 'title', 'comment', 'ip_address']
    ordering = ('-timestamp',)


class TypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name', 'plural_name']

class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

class ReportUploadAdmin(admin.ModelAdmin):
    list_display = ['created', 'type', 'unknown_upc_count']
    ordering = ('-created',)
    list_filter = ['type']
    date_hierarchy = 'created'

admin.site.register(Category, CategoryAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(ReportUpload, ReportUploadAdmin)
admin.site.register(Tag, TagAdmin)
