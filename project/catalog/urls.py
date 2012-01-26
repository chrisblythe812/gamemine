from django.conf.urls.defaults import * #@UnusedWildImport
from models import Category
from views.catalog import CATALOG_FILTERS

category_pattern = '(?P<slug>' + '|'.join(Category.list_slugs()) + ')';
filter_pattern = '(?P<filter>' + '|'.join([x[0] for x in CATALOG_FILTERS]) + ')'
item_pattern = "(?P<item_slug>.*?)/Products/Detail/(?P<id>[1-9][0-9]*)"

item_actions = ['hint-details', 'details', 'muze-description', 'get-more-reviews', 'media-details', 'get-all-reviews', 'get-helpful-reviews']

urlpatterns = patterns('project.catalog.views',
    url('^Browse-Games/$', 'index_new', name='index', kwargs={'slug': None}),
    url('^%s/$' % category_pattern, 'index_new', name='category'),
    url('^%s/Sub/$' % category_pattern, 'index_new', name='category_sub'),

#    url('^Browse-Games/%s/$' % filter_pattern, 'category', name='index', kwargs={'slug': None}),
#    url('^Browse-Games/$', 'category', name='index', kwargs={'slug': None, 'filter': None}),
#
#    url('^%s/%s/$' % (category_pattern, filter_pattern), 'category', name='category'),
#    url('^%s/$' % category_pattern, 'category', name='category', kwargs={'filter': None}),

    url('^%s/$' % item_pattern, 'item', name='item'),
    url('^%s/(?P<action>%s)/$' % (item_pattern, '|'.join(item_actions)), 'item_action', name='item_action'),

    url('Browse-Games/_/popular-by-publisher/(?P<id>[1-9][0-9]*)/$', 'popular_by_publisher', name='popular-by-publisher'),
    url('Browse-Games/_/popular-by-category/%s/$' % category_pattern, 'popular_by_category', name='popular-by-category'),

    url('Rate/(?P<id>[1-9][0-9]*)/(?P<rating>[1-5]*)/$', 'rate', name='rate'),
    url('Rate/(?P<id>[1-9][0-9]*)/Delete/$', 'delete_rate', name='delete_rate'),
    url('Review/Vote/(?P<id>[1-9][0-9]*)/(?P<vote>yes|no)/$', 'mark_useful', name='mark_useful'),
    url('Review/(?P<id>[1-9][0-9]*)/Delete/$', 'delete_review', name='delete_review'),
    url('Review/(?P<id>[1-9][0-9]*)/Edit/$', 'edit_review', name='edit_review'),

    url('ESRB/$', 'esrb', name='esrb'),
)

#urlpatterns += patterns('django.contrib.auth.views',
#    url(r'^login$', 'login', name='login', kwargs={'template_name': 'members/login.html'}),
#)
