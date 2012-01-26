from django.conf.urls.defaults import * #@UnusedWildImport

urlpatterns = patterns('project.buy_orders.views',
#    url('^List/$', 'list', name='list'),
#    url('^List/Add/(?P<id>[1-9][0-9]*)/$', 'add_to_list', name='add_to_list'),
    url('^Buy/List/Remove/(?P<id>[1-9][0-9]*)/$', 'remove_from_list', name='remove_from_list'),
    url('^Buy_Confirmation/Summary/$', 'confirmation_summary', name='confirmation_summary'),
)
