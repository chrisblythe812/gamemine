from logging import debug #@UnusedImport

from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.core.urlresolvers import reverse
from django.template import loader
from django.template.context import RequestContext
from django.http import Http404, HttpResponseBadRequest
from django.conf import settings
from django.template import defaultfilters

from django_snippets.views import simple_view, JsonResponse
from django_snippets.thirdparty.views import secure

from project.catalog.models import Item
from forms import AddItemConditionForm
from project.buy_orders.models import BuyCartItem, BuyList
from project.cart.wizards import AuthenticatedCheckoutWizard,\
    NonAuthenticatedCheckoutWizard
import decimal
from project.members.models import ProfileEntryPoint



def get_melissa():
    if settings.MELISSA_CONFIG['use_melissa']:
        from melissadata import Melissa
        return Melissa(settings.MELISSA_CONFIG)
    else:
        return None

@secure
@simple_view('cart/index.html')
def index(request):
    if not request.user.is_authenticated() and request.cart.size == 0:
        return redirect('catalog:index')


def add(request, id):
    item = get_object_or_404(Item, id=id)
    if not request.is_ajax():
        return redirect(item.get_absolute_url())

    if request.method == 'POST':
        submit = request.POST.get('submit', 'cart')
        res = {}
        form = AddItemConditionForm(request.POST)
        if form.is_valid():
            is_new = item.is_prereleased_game() or form.cleaned_data['condition'] == 'new'
            if submit == 'cart':
                request.cart.push_item(request, item, inc_quantity=1, is_new=is_new)
                res['redirect_to'] = reverse('cart:index')
            else:
                buy_alert = submit == 'buy-alert'
                BuyList.add_to_list(request, item, is_new, buy_alert=buy_alert)
                if request.user.is_authenticated():
                    res['redirect_to'] = reverse('members:buy_list')
                else:
                    request.session['entry_point'] = ProfileEntryPoint.Buy
                    res['redirect_to'] = reverse('members:create_account')
        else:
            res['form'] = loader.render_to_string('cart/add.dialog.html',
                                                  {'form': form, 'item': item, },
                                                  RequestContext(request))
        return JsonResponse(res)

    form = AddItemConditionForm()
    return render_to_response('cart/add.dialog.html',
                          {'form': form, 'item': item, 'check_used_by_default': request.GET.get('is_pre_owned'),},
                          context_instance=RequestContext(request))


def update(request, id):
    if not request.is_ajax():
        return redirect('cart:index')
    item = request.cart.items.filter(id=id)
    if item.count() == 0:
        raise Http404()
    item = item[0]

    if request.method == 'POST':
        res = {}
        form = AddItemConditionForm(request.POST)
        if form.is_valid():
            is_new = item.item.is_prereleased_game() or form.cleaned_data['condition'] == 'new'
            item.is_new = is_new
            item.user_session_price = item.item.retail_price_new if is_new else item.item.retail_price_used
            item.save()
            res['redirect_to'] = reverse('cart:index')
        else:
            res['form'] = loader.render_to_string('cart/update-cart.dialog.html',
                                                  {'form': form, 'item': item.item, 'cart_item': item },
                                                  RequestContext(request))
        return JsonResponse(res)


    form = AddItemConditionForm()
    return render_to_response('cart/update-cart.dialog.html',
                          {'form': form, 'item': item.item, 'cart_item': item },
                          context_instance=RequestContext(request))


@secure
def remove(request, id):
    if not settings.DEBUG and not request.is_ajax():
        return HttpResponseBadRequest()
    item = get_object_or_404(BuyCartItem, id=id)
    if item.cart != request.cart:
        raise Http404()
    request.cart.remove(item)
#    if request.cart.size == 0:
#        return JsonResponse({'redirect_to': reverse('members:buy_list'), })
    return JsonResponse({
        'cart': {
            'size': request.cart.size,
            'total': '$' + defaultfilters.floatformat(request.cart.total, 2),
        },
        'html': loader.render_to_string('cart/partials/cart-table.html',
                                        {},
                                        RequestContext(request)),
    })


@secure
@simple_view('cart/checkout/non_authenticated_choice.html')
def checkout(request):
    if not request.is_ajax() or request.cart.items.all().count() == 0:
        return redirect('cart:index')
    if request.user.is_authenticated():
        return AuthenticatedCheckoutWizard.create(request)(request)
    else:
        do = request.GET.get('do')
        if do == 'signup' or request.method == 'POST':
            return NonAuthenticatedCheckoutWizard.create(request)(request)


@simple_view('cart/index.html')
def checkout_complete(request):
    pass


def update_quantity(request):
    if not request.is_ajax():
        return redirect('cart:index')

    results = {}
    for k, v in request.POST.items():
        if k.startswith('i-'):
            try:
                k = int(k[2:])
                results[k] = v
            except:
                pass
    for item in request.cart.items.all():
        if item.id in results:
            try:
                quantity = int(results[item.id])
                if quantity == 0:
                    item.delete()
                else:
                    item.quantity = quantity
                    item.save()
            except:
                pass
    request.cart.recalc()
    if request.cart.size == 0:
        return JsonResponse({'redirect_to': reverse('catalog:index'), })

    return JsonResponse({
        'cart': {
            'size': request.cart.size,
            'total': '$' + defaultfilters.floatformat(request.cart.total, 2),
        },
        'html': loader.render_to_string('cart/partials/cart-table.html',
                                        {},
                                        RequestContext(request)),
    })


def apply_credits(request):
    if not request.is_ajax():
        return redirect('cart:index')

    try:
        amount = decimal.Decimal(request.POST.get('amount'))
    except:
        return redirect('cart:index')
    request.cart.applied_credits = amount
    request.cart.save()
    return JsonResponse({
        'cart': {
            'size': request.cart.size,
            'total': '$' + defaultfilters.floatformat(request.cart.total, 2),
        },
        'html': loader.render_to_string('cart/partials/cart-table.html',
                                        {},
                                        RequestContext(request)),
    })
