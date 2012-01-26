from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('project.os3marketing.views',
   url(r'^site/(?P<slug>[-\w]+)/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$','opened_on_site',name='os3marketing_opened_on_site' ),
   url(r'^unsubscribe/(?P<slug>[-\w]+)/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$','mailinglist_unsubscribe', name='os3marketing_mailinglist_unsubscribe'),    
   url(r'^email/(?P<slug>[-\w]+)/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$','opened_email', name='os3marketing_opened_email'),          
   url(r'^link/(?P<slug>[-\w]+)/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/(?P<link_id>\d+)/$','clicked_link',name='os3marketing_clicked_link'),
)

