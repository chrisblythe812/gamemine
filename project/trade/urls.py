from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns('project.trade.views',
    url('^Trade/Check-UPC/(?P<id>[1-9][0-9]*)/$', 'check_upc', name='check_upc'),
    url('^Trade/Add/(?P<id>[1-9][0-9]*)/$', 'add', name='add'),
    url('^Trade/Change/(?P<id>[1-9][0-9]*)/$', 'change_item', name='change_item'),
    url('^Trade/Cart/$', 'cart', name='cart'),
    url('^Trade/Address/$', 'address', name='address'),
    url('^Trade/Carrier/$', 'carrier', name='carrier'),
    url('^Trade/List/$', 'list', name='list'),
    url('^Trade_Confirmation/Summary/$', 'print_sl', name='print_sl'),
    url('^Trade/Shipping-Slip/(?P<order_number>\d+)/$', 'shipping_slip', name='shipping_slip'),
    url('^Trade/Finish/$', 'finish', name='finish'),
    url('^Trade/List/$', 'list', name='list'),
    url('^Trade/Remove/(?P<item_id>\d+)/$', 'remove', name='remove'),
    url('^Trade/RemoveAll/$', 'remove_all', name='remove_all'),

    url('^Login/$', 'login', name='login'),
    url('^Order-BarCode/(?P<order_id>[1-9][0-9]*)/$', 'order_barcode', name='order_barcode'),
)

