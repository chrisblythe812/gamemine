from django.conf.urls.defaults import * #@UnusedWildImport


urlpatterns = patterns('project.cart.views',
    url('^$', 'index', name='index'),
    url('^Add/(?P<id>[1-9][0-9]*)/$', 'add', name='add'),
    url('^Remove/(?P<id>[1-9][0-9]*)/$', 'remove', name='remove'),
    url('^Update/(?P<id>[1-9][0-9]*)/$', 'update', name='update'),
    url('^Checkout/$', 'checkout', name='checkout'),
    url('^Checkout/Complete/$', 'checkout_complete', name='checkout_complete'),
    url('^Update-Quantity/$', 'update_quantity', name='update_quantity'),
    url('^Apply-Credits/$', 'apply_credits', name='apply_credits'),
)
