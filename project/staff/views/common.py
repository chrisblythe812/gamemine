from logging import debug #@UnusedImport

from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.conf import settings
from django.db.models import Q, Count

from django_snippets.views import simple_view
from django_snippets.views import paged
from django_snippets.views import JsonResponse

from project.members.models import Profile
from project.catalog.models import Item
from project.inventory.models import Purchase
from project.staff.views import staff_only
from project.staff.urls import staff_main_menu
from project.rent.models import RentalPlanStatus,MemberRentalPlan


@staff_only
@simple_view('staff/index.html')
def index(self):
    return {}


@staff_only
@simple_view('staff/customer.html')
@paged('profiles',50)
def customer(request):
    from project.staff.forms import CustomerSearchForm

    qs = Profile.objects.exclude(user=None).order_by('id')
    form = CustomerSearchForm(request.GET)
    if form.is_valid():
        name = form.cleaned_data.get('name')
        if name:
            qs = qs.filter(Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name))

        email = form.cleaned_data.get('email')
        if email:
            qs = qs.filter(user__email__icontains=email)

        campaign = form.cleaned_data.get('campaign')
        if campaign is not None:
            qs = qs.filter(campaign_cid=campaign.cid)

        plan = form.cleaned_data.get('plan')
        if plan:
            qs = qs.filter(user__memberrentalplan__plan=plan.plan)
            qs = qs.exclude(user__memberrentalplan__status__in=[RentalPlanStatus.AutoCanceled, RentalPlanStatus.Canceled])

        joined_from = form.cleaned_data.get('joined_from')
        if joined_from:
            qs = qs.filter(user__date_joined__gte=joined_from)

        joined_to = form.cleaned_data.get('joined_to')
        if joined_to:
            qs = qs.filter(user__date_joined__lte=joined_to)

        buy_orders = form.cleaned_data.get('buy_orders')
        if buy_orders != '':
            qs = qs.annotate(buyorders=Count('user__buyorder'))
            if buy_orders:
                qs = qs.filter(buyorders__gt=0)
            else:
                qs = qs.filter(buyorders=0)

        trade_orders = form.cleaned_data.get('trade_orders')
        if trade_orders != '':
            qs = qs.annotate(tradeorders=Count('user__tradeorder'))
            if trade_orders:
                qs = qs.filter(tradeorders__gt=0)
            else:
                qs = qs.filter(tradeorders=0)

        zip = form.cleaned_data.get('zip')
        if zip != '':
            qs = qs.filter(shipping_zip__icontains=zip)

        address = form.cleaned_data.get('address')
        if address != '':
            qs = qs.filter(Q(shipping_address1__icontains=address) | Q(shipping_city__icontains=address))

        status = form.cleaned_data.get('status')

        if status != '':
#            qs = qs.filter(user__memberrentalplan__status=status)
            qs = qs.filter(user__pk__in=MemberRentalPlan.objects.filter(status=status).values('user').order_by('user').query)
#
#        cancellations = form.cleaned_data.get('cancellations')
#        if cancellations != '':
#            qs = qs.annotate(tradeorders=Count('user__tradeorder'))
    return {
        'paged_qs': qs,
        'form': form,
    }


@simple_view('staff/fulfillment.html')
def fulfillment(self):
    return {}


@staff_only
def page(request, path):
    user = request.user
    profile = user.get_profile()
    if not user.is_superuser and not staff_main_menu.is_item_accessible(profile.group, '/Staff/%s/' % path):
        return HttpResponseForbidden('Access Denied')

    path = map(lambda x: x.encode('ascii'), path.lower().replace('-', '_').split('/'))
    path = [path[0], '__'.join(path[1:])]
    import_path = ['project', 'staff', 'views'] + path
    try:
        module = __import__('.'.join(import_path[:-1]), fromlist=[import_path[-1]], level=0)
        func = getattr(module, import_path[-1])
    except ImportError, e:
        if settings.DEBUG:
            raise Http404(e)
        raise Http404()
    except AttributeError, e:
        if settings.DEBUG:
            raise Http404(e)
        raise Http404()

    res = func(request, path=path)
    if isinstance(res, HttpResponse):
        return res
    if len(res) == 2:
        cnx, template = res
        paged_data = None
    else:
        cnx, template, paged_data = res
    if isinstance(cnx, HttpResponse):
        return cnx
    context = {
        'page_class': 'staff-page-' + '-'.join(path),
    }
    path = map(lambda x: x.replace('__', '/'), path)
    context.update(cnx or {})
    template = template or 'staff/' + '/'.join(path) + '.html'
    if paged_data:
        def wrapper(request, *args, **kwargs): return context
        context = paged(*paged_data)(wrapper)(request)
        return render_to_response(template, context, RequestContext(request))
    else:
        return render_to_response(template, context, RequestContext(request))

@staff_only
def check_upc(request, upc):
    item = Item.find_by_upc(upc)
    if item:
        return JsonResponse({'success': True, 'title': item.name, 'platform': unicode(item.category)})
    else:
        return JsonResponse({'success': False})

@staff_only
@simple_view('staff/purchase_order.html')
def purchase_order(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    return {
        'purchase': purchase,
        'post_address': settings.GAMEMINE_POST_ADDRESS,
        'shipping_address': settings.GAMEMINE_SHIPPING_ADDRESS,
    }
