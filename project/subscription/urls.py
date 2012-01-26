from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('project.subscription.views',
    url('^Subscribe/$', 'subscribe', name='subscribe'),
    url('^Thank-You/$', 'thankyou', name='thankyou'),
    url('^Confirm/(?P<guid>.*)/$', 'confirm', name='confirm'),
    url('^Sign-Up/$', 'signup', name='signup'),
)
