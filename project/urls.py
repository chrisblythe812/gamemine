from django.conf.urls.defaults import * #@UnusedWildImport
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

import project.new_views

simple_pages = ['Terms', 'Privacy', 'UPC', 'How-It-Works', 'Help-FAQs', 'Free-Shipping']

if settings.DEBUG:
    simple_pages.append('Test')

urlpatterns = patterns('',
    (r'^tinymce/', include('tinymce.urls')),
    (r'^area51/filebrowser/', include('filebrowser.urls')),
    url(r'^newsletter/', include('project.os3marketing.urls')),
    (r'^area51/', include(admin.site.urls)),
    (r'^grappelli/', include('grappelli.urls')),
#    (r'^area51/admin_tools/', include('admin_tools.urls')),
    (r'^area51/orders/pending/$', 'project.buy_orders.views.pending'),
    (r'^area51/rent/pick-list/$', 'project.rent.admin.pick_list'),
    (r'^area51/rent/create-order/(?P<id>[1-9][0-9]*)/$', 'project.rent.admin.create_order'),
#    (r'^area51/rent/order/(?P<id>[1-9][0-9]*)/$', 'project.rent.admin.view_order'),
    (r'^area51/rent/order/(?P<id>[1-9][0-9]*)/generate_labels/$', 'project.rent.admin.generate_order_labels'),

    url(r'^Staff/', include('project.staff.urls', namespace='staff')),
    url(r'^Subscription/', include('project.subscription.urls', namespace='subscription')),

    url(r'^(?P<path>googlee8702d2c6fbb89d7\.html)$', 'django.views.static.serve', {'document_root': settings.PROJECT_ROOT + '/templates/static'}),
)


if True: #not settings.MAINTENANCE:
    urlpatterns += patterns('',
        url('^Banners/Balalayka/$', 'project.banners.views.balalayka'),

        url(r'campaign$', 'project.views.campaign'),

        url(r'^Oups/$', 'project.views.oups', name='oups'),
        url(r'^Seals/$', 'project.views.seals', name='seals'),
        url(r'^Seals/(?P<t>[\w_-]+)$', 'project.views.seals', name='seals_bg'),
        url(r'^Deck-the-Halls/$', 'project.views.deck_the_halls', name='deck_the_halls'),

        url(r'^$', project.new_views.IntroView.as_view(), name='index'),

        url(r'^Buy/$', 'project.views.buy_intro2', name='buy_intro'),
#        url(r'^Buy-New/$', 'project.views.buy_intro2'),
        url(r'^Trade/$', 'project.views.trade_intro2', name='trade_intro'),
#        url(r'^Trade-New/$', 'project.views.trade_intro2'),
        url(r'^Rent/$', project.new_views.RentIntroView.as_view(), name='rent_intro'),

        url(r'^Rent/Destination/$', 'project.views.rent_intro2', name='rent_intro2'),
        url(r'^What-is-My-Game-Worth/$', 'project.views.wimgw', name='wimgw'),

        url(r'^', include('project.members.urls', namespace='members')),
        url(r'^', include('project.catalog.urls', namespace='catalog')),
        url(r'^Cart/', include('project.cart.urls', namespace='cart')),
        url(r'^', include('project.trade.urls', namespace='trade')),
        url(r'^', include('project.buy_orders.urls', namespace='buy')),
        url(r'^', include('project.rent.urls', namespace='rent')),
        url(r'^', include('project.new_rent.urls', namespace='new_rent')),
        url(r'^Search/', include('project.search.urls', namespace='search')),
        url(r'^', include('project.claims.urls', namespace='claims')),

        url(r'^reviews/', include('project.reviews.urls')),

        url(r'^crm/', include('project.crm.urls', namespace='crm')),

        # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
        # to INSTALLED_APPS to enable admin documentation:
        # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

        # Uncomment the next line to enable the admin:

        url(r'^(?P<page>%s)/$' % '|'.join(simple_pages), 'project.views.simple_page', name='simple-page'),
        url(r'^Inventory/Tyvek/(?P<inventory_id>\d+)/$', 'project.inventory.views.inventory_tyvek', name='inventory_tyvek'),
    )
else:
    urlpatterns += patterns('',
        url(r'^.*$', 'project.views.maintenance'),
    )

urlpatterns += patterns('',
    (r'^sentry/', include('sentry.web.urls')),
)

# Serving media on dev, static is served automatically
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler500 = 'project.views.page500'
