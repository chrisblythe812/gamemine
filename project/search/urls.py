from django.conf.urls.defaults import * #@UnusedWildImport


urlpatterns = patterns('project.search.views',
    url(r'^$', 'search', name='search'),
    url(r'^By-UPC/$', 'by_upc', name='by-upc'),
    url(r'^By-UPC/All/$', 'by_upc2', name='by-upc-all'),
    url(r'^Quick/$', 'quick', name='quick'),
)
