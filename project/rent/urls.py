from django.conf.urls.defaults import * #@UnusedWildImport


urlpatterns = patterns('project.rent.views',
    url(r'^Rent/Add/(?P<id>[1-9][0-9]*)/$', 'add', name='add'),
    url(r'^Rent/Remove/(?P<id>[1-9][0-9]*)/$', 'remove', name='remove'),
    url(r'^Rent/Move-Up/(?P<id>[1-9][0-9]*)/$', 'move_up', name='move_up'),
    url(r'^Rent/Move-Down/(?P<id>[1-9][0-9]*)/$', 'move_down', name='move_down'),
    url(r'^Rent/Move-To/(?P<id>[1-9][0-9]*)/(?P<pos>[0-9]+)/$', 'move_to', name='move_to'),
    url(r'^Rent/Add-Note/(?P<id>[1-9][0-9]*)/$', 'add_note', name='add_note'),
    url(r'^Rent_Confirmation/Summary/$', 'confirmation', name='confirmation'),
)
