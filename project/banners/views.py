from django_snippets.views import simple_view
from django.shortcuts import redirect
from django.conf import settings
from django.core.urlresolvers import reverse

from django_snippets.views.json_response import JsonResponse

from project.catalog.models.items import Item
from project.rent.models import MemberRentalPlan
from project.tds.utils import is_eligible_for_free_trial


@simple_view('banners/test.html')
def balalayka(request):
    if request.is_ajax():
        def img(n):
            f = settings.STATIC_URL + 'img/banners/balalayka/%s.jpg'
            return f % (n + '-b'), f % (n + '-s')

        def g(id):
            try:
                return Item.objects.get(id=id).get_absolute_url()
            except Item.DoesNotExist:
                return None

        banners = [ 
                {
                    'banner_class': 'banner-rent-1',
                    'links': [('/Rent/SignUp/', 'link-dialog')],
                    'images': img('rent-1'),
                },
                {
                    'banner_class': 'banner-rent-2',
                    'links': [('/Rent/Destination/', None)],
                    'images': img('rent-2'),
                },
                {
                    'banner_class': 'banner-freetrial',
                    'links': [('/Rent/SignUp/', 'link-dialog')],
                    'images': img('freetrial'),
                },
                {
                    'banner_class': 'banner-wimgw',
                    'links': [(g(id), None) for id in [100000325, 10000040, 100000013]],
                    'images': img('wimgw'),
                },
                {
                    'banner_class': 'banner-trade',
                    'links': [('/Trade/', None)],
                    'images': img('trade'),
                },
                {
                    'banner_class': 'banner-newsletter',
                    'links': [(reverse('subscription:signup'), 'link-dialog')],
                    'images': img('newsletter'),
                },
                {
                    'banner_class': 'banner-buy',
                    'links': [('/Buy/', None)],
                    'images': img('buy'),
                },
            ]
        if request.user.is_authenticated():
            if MemberRentalPlan.get_current_plan(request.user):
                banner_set = [1, 3, 4, 6]
            else:
                banner_set = [0, 3, 4, 6]
        else:
            if 'subscription-done' in request.COOKIES:
                banner_set = [0, 3, 4, 6]
            else:
                banner_set = [0, 3, 4, 5, 6]
                if is_eligible_for_free_trial(request):
                    banner_set[0] = 2

        return JsonResponse({
            'banners': [banners[x] for x in banner_set],})
    if not settings.DEBUG:
        return redirect('/')
