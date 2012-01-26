from django.conf.urls.defaults import * #@UnusedWildImport


urlpatterns = patterns('project.crm.views',
    url('^ifn/$', 'ifn', name='ifn'),
)
