from logging import debug #@UnusedImport

from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from django.template import loader
from django.template.context import RequestContext
from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from django_snippets.views import simple_view, JsonResponse

from wizards import NonAuthenticatedTradeWizard

from project.rent.models import RentList
from project.catalog.models.items import Item
from project.trade.forms import CheckUPCForm, AddItemCompletenessForm, AddressForm
from project.trade.models import TradeListItem, TradeCart, TradeOrder
from project.members.models import ProfileEntryPoint
from project.banners.models import ListPageBanner


def get_melissa():
    if settings.MELISSA_CONFIG['use_melissa']:
        from melissadata import Melissa
        return Melissa(settings.MELISSA_CONFIG)
    else:
        return None

def check_upc(request, id):
    item = get_object_or_404(Item, id=id)
    if not request.is_ajax():
        return redirect(item.get_absolute_url())

    if request.method == 'POST':
        dest = request.POST.get('dest', '/')

        res = {}
        form = CheckUPCForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated():
                res['close'] = True
                res['redirect_to'] = dest
            else:
                return login(request)
        else:
            if request.user.is_authenticated():
                dest_wizard = False
                dest = reverse('trade:cart')
            else:
                dest_wizard = True
                dest = reverse('trade:login')

            ctx = {
                'form': form,
                'item': item,
                'dest': dest,
                'dest_wizard': dest_wizard,
            }

            res['form'] = loader.render_to_string('trade/check_upc.html', ctx, RequestContext(request))
        return JsonResponse(res)

    form = CheckUPCForm()
    return render_to_response('trade/check_upc.html',
                              {'form': form, 'item': item, },
                              RequestContext(request))

def add(request, id):
    item = get_object_or_404(Item, id=id)
    if not request.is_ajax():
        return redirect(item.get_absolute_url())

    if request.method == 'POST':
        dest_wizard = False
        form = AddItemCompletenessForm(request.POST)
        if form.is_valid():
            is_complete = form.cleaned_data['completeness'] == 'cg'

            is_valid_choice = True
            if not is_complete:
                if not request.user.is_authenticated():
                    is_valid_choice = False
                elif not request.user.get_profile().has_game_perks():
                    is_valid_choice = False

            if is_valid_choice:
                if request.POST.get('submit') == 'list':
                    # add to list
                    TradeListItem.add(request, item, is_complete)
                    if request.user.is_authenticated():
                        return JsonResponse({'redirect_to': reverse('trade:list')})
                    else:
                        request.session['entry_point'] = ProfileEntryPoint.Trade
                        return JsonResponse({'goto_url': reverse('members:create_account')})
                else:
                    # add to cart
                    if not item.trade_flag:
                        return redirect(item.get_absolute_url())
                    cart = TradeCart.get(request)
                    cart.push_item(request, item, inc_quantity=1, is_complete=is_complete)
                    if request.user.is_authenticated():
                        dest = reverse('trade:cart')
                    else:
                        request.session['entry_point'] = ProfileEntryPoint.Trade
                        return JsonResponse({'goto_url': reverse('members:create_account')})
#                        dest_wizard = True
#                        dest = reverse('trade:login')

                template = 'trade/check_upc.html'
                form = CheckUPCForm()
            else:
                template = 'trade/add.dialog.html'
                dest = None
        else:
            template = 'trade/add.dialog.html'
            dest = None

        ctx = {
            'form': form,
            'item': item,
            'dest': dest,
            'dest_wizard': dest_wizard,
        }

        res = {}
        res['form'] = loader.render_to_string(template, ctx, RequestContext(request))
        return JsonResponse(res)

    form = AddItemCompletenessForm()
    return render_to_response('trade/add.dialog.html',
                          {'form': form, 'item': item, },
                          context_instance=RequestContext(request))

@simple_view('trade/authentication/authentication.html')
def login(request):
    if request.user.is_authenticated():
        return redirect(reverse('trade:cart'))

    if request.GET.get('do') == 'signup' or request.method == 'POST':
        return NonAuthenticatedTradeWizard.create(request)(request)

@login_required
def change_item(request, id):
    filter = {'pk': id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    list_item = get_object_or_404(TradeListItem, **filter)
    if not request.is_ajax():
        return redirect(list_item.item.get_absolute_url())

    if request.method == 'POST':
        res = {}

        form = AddItemCompletenessForm(request.POST)
        if form.is_valid():
            list_item.is_complete = form.cleaned_data['completeness'] == 'cg'
            list_item.save()
            res['close'] = True
            res['redirect_to'] = reverse('trade:list')
        else:
            res['form'] = loader.render_to_string('trade/change-item.html',
                                                  {'item': list_item.item, 'list_item': list_item, },
                                                  RequestContext(request))
        return JsonResponse(res)

    form = AddItemCompletenessForm()
    return render_to_response('trade/change-item.html',
                              {'item': list_item.item, 'list_item': list_item, },
                              context_instance=RequestContext(request))

def str2int(s):
    try:
        return int(s)
    except ValueError:
        return 0

@login_required
@simple_view('trade/cart.html')
def cart(request):
    cart = TradeCart.get(request)
    cart_items = cart.items.all()

    if request.method == 'POST':
        for item in cart_items:
            q = str2int(request.POST.get('i-%d' % item.id))
            if q:
                item.quantity = q
                item.save()
            else:
                item.delete()
        cart._recalc_size()
        cart.save()
        if not request.is_ajax():
            return redirect(reverse('trade:address'))


    total_amount = sum([item.quantity * item.user_session_price for item in cart_items])
    ctx = {
        'cart': cart,
        'cart_items': cart.get_items(),
        'total_quantity': cart.size,
        'total_amount': total_amount,
    }
    if request.is_ajax():
        return render_to_response('trade/partials/cart_grid.html', ctx, RequestContext(request))
    return ctx


@login_required
@simple_view('trade/address.html')
def address(request):
    profile = request.user.get_profile()

    if request.method == 'POST':
        if 'ship-from-stored-address' in request.POST:
            return redirect(reverse('trade:carrier'))
        else:
            def create_form(data):
                return AddressForm(data,
                                   melissa=get_melissa(),
                                   request=request,
                                   activate_correction=True)


            form = create_form(request.POST)
            if form.is_valid():
                profile.set_name_data(form.cached_name)
                profile.set_shipping_address_data(form.cached_address)
                profile.phone = form.cached_phone
                profile.save()
                return redirect(reverse('trade:carrier'))
            else:
                errors = []
                for n, f in form.fields.items():
                    if form.errors.get(n):
                        errors.append(mark_safe(u'Error &mdash; Your %s is incorrect' % f.label))
                e = form.errors.get('__all__')
                if e:
                    errors.append(e[0])
                form.form_error = (errors or [None])[0]
                debug(form.form_error)
                if hasattr(form, 'correction_data'):
                    form = create_form(form.correction_data)
                    form.correction_warning = True
    else:
        form = AddressForm()

    ctx = {
        'form': form,
        'fullname': profile.get_full_name(),
        'has_address': profile.has_shipping_address(),
    }
    address = profile.get_shipping_address_data()
    ctx.update(address)
    return ctx

POSTAL_CARRIERS = ['ups', 'usps', 'custom']

@login_required
@simple_view('trade/postal-carrier.html')
def carrier(request):
    if request.method == 'POST':
        carrier = request.POST.get('carrier')
        if carrier in POSTAL_CARRIERS:
            request.session['trade_postal_carrier'] = carrier
            return redirect(reverse('trade:print_sl'))
    return {}


@login_required
@simple_view('members/lists/trade.html')
def list(request):
    trade_list = TradeListItem.get(request)
    trade_list_total = sum([item.get_price() for item in trade_list])

    if request.method == 'POST':
        # add to cart
        cart = TradeCart.get(request)
        for item in trade_list:
            if ('item-%d' % item.id) in request.POST:
                cart.push_item(request, item.item, inc_quantity=1, is_complete=item.is_complete)
                item.delete()
        return redirect(reverse('trade:cart'))

    orders = TradeOrder.objects.filter(user=request.user).extra(where=["exists(select * from trade_tradeorderitem where order_id=trade_tradeorder.id and processed='f')"])

    return {
        'buy_list': request.buy_list,
        'rent_list': RentList.get(request.user, request),
        'trade_orders': orders,
        'trade_list': trade_list,
        'trade_list_total': trade_list_total,
        'pending_credits': request.user.get_profile().get_pending_credits(),
        'banners': [ListPageBanner.objects.get_random()],
    }

@login_required
@simple_view('trade/print.html')
def print_sl(request):
    profile = request.user.get_profile()
    cart = TradeCart.get(request)

    if not cart.size:
        if not settings.DEBUG:
            return redirect(reverse('trade:cart'))
        else:
            order = (TradeOrder.objects.filter(user=request.user) or (None, ))[0]
            if not order:
                return redirect(reverse('trade:cart'))
    else:
        if not profile.has_shipping_address():
            return redirect(reverse('trade:address'))
        if ('trade_postal_carrier' not in request.session) or (request.session['trade_postal_carrier'] not in POSTAL_CARRIERS):
            return redirect(reverse('trade:carrier'))

        order = TradeOrder.create(request, cart)

    try:
        order.send_order_confirmation()
    except Exception, e:
        debug(e)

    return {
        'mailing_date': order.get_mailing_date().strftime('%B %d, %Y'),
        'gm_address': settings.GAMEMINE_POST_ADDRESS,
        'total': order.total,
        'shipping_reimbursements': order.get_shipping_reimbursements(),
        'quantity': order.size,
        'order_number': '%08d' % order.id,
        }

@login_required
def finish(request):
    return redirect(reverse('trade:list'))

@login_required
@simple_view('trade/shipping-slip.html')
def shipping_slip(request, order_number):
    order_number = int(order_number, 10)
    order = get_object_or_404(TradeOrder, id=order_number, user=request.user)
    return {
        'order': order,
        'order_date': order.create_date.strftime('%x'),
        'order_number': order.order_no(),
        'gm_address': settings.GAMEMINE_POST_ADDRESS,
        'items': order.items.all(),
        'mailing_date': order.get_mailing_date().strftime('%B %d, %Y'),
    }

def order_barcode(request, order_id):
    if not request.user.is_authenticated():
        raise Http404()
    order = get_object_or_404(TradeOrder, id=order_id, user=request.user)
    number = order.order_no()

    from code128 import Code128
    bar = Code128()
    image = bar.getImage(number, 70, "png")

    response = HttpResponse(mimetype="image/png")
    image.save(response, 'PNG')
    return response

def  _trade_action(request):
    if request.is_ajax():
        from project.members.context_processors import core
        list = TradeListItem.get(request)
        context = {
            'trade_list': list,
            'trade_list_total': sum([item.get_price() for item in list])
        }
        res = {
            'trade_list': {
                'size': list.count(),
            },
            'lists_size': core(request)['lists_size'],
            'html': render_to_string('members/lists/trade_list_grid.html', context, RequestContext(request)),
        }
        return JsonResponse(res)
    return redirect('trade:list')


@login_required
def remove(request, item_id):
    filter = {'pk': item_id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    item = get_object_or_404(TradeListItem, **filter)
    item.delete()
    return _trade_action(request)


@login_required
def remove_all(request):
    filter = {}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    TradeListItem.objects.filter(**filter).delete()
    return _trade_action(request)
