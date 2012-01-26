from django.conf.urls.defaults import * #@UnusedWildImport


urlpatterns = patterns('project.claims.views',
    url(r'^Account/Report-Problems/(?P<sphere>Buy)/(?P<id>[1-9][0-9]*)/(?P<claim>Game-Is-Damaged|Wrong-Game|Havent-Receive-Game-Yet)/$', 'post_claim', name='post_claim'),
    url(r'^Account/Report-Problems/(?P<sphere>Trade)/(?P<id>[1-9][0-9]*)/(?P<claim>Gamemine-Not-Receive-Trade-Game|Wrong-Trade-Value-Credit)/$', 'post_claim', name='post_claim'),
    url(r'^Account/Report-Problems/(?P<sphere>Rent)/(?P<id>[1-9][0-9]*)/(?P<claim>Game-Is-Damaged|Wrong-Game|Mailer-Is-Empty|Havent-Receive-Game-Yet|Gamemine-Not-Receive-Game)/$', 'post_claim', name='post_claim'),
)
