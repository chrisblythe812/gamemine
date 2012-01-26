from logging import debug #@UnusedImport
from datetime import datetime, timedelta

from django_snippets.views import simple_view
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction

from project.claims.forms import GameIsDamagedForm, WrongGameForm,\
    MailerIsEmptyForm, DontReceiveForm, GamemineNotRecieveForm,\
    GamemineNotRecieveTradeGameForm, WrongTradeValueCreditForm
from project.claims.models import SPHERE_REVERSED_DICT, ClaimType, SphereChoice
from project.rent.models import RentOrder, RentOrderStatus
from project.buy_orders.models import BuyOrderItem
from project.trade.models import TradeOrderItem
from project.inventory.models import InventoryStatus
from project.crm.models import CaseStatus


CLAIM_FORMS = {
    'Game-Is-Damaged': GameIsDamagedForm,
    'Wrong-Game': WrongGameForm,
    'Mailer-Is-Empty': MailerIsEmptyForm,
    'Havent-Receive-Game-Yet': DontReceiveForm,
    'Gamemine-Not-Receive-Game': GamemineNotRecieveForm,
    'Gamemine-Not-Receive-Trade-Game': GamemineNotRecieveTradeGameForm,
    'Wrong-Trade-Value-Credit': WrongTradeValueCreditForm,
}


@simple_view('claims/rent_claim.html')
def do_rent_claim(request, item):
    user = request.user
    shipped_date = item.date_shipped
    less_than_7_days = (shipped_date or datetime.now()).date() > (datetime.now().date() - timedelta(7))
    order = item

    if order.status == RentOrderStatus.Returned:
        raise Http404()

    return {
        'shpere': 'Rent',
        'game': item.item,
        'order': order,
        'item': item,
        'less_than_7_days': less_than_7_days,
        'shipped_date': shipped_date,
        'shipped_date_plus_7': (shipped_date or datetime.now()) + timedelta(7),
        'forms': {
            'game_is_damaged': GameIsDamagedForm.create(user, item),
            'wrong_game': WrongGameForm.create(user, item),
            'mailer_is_empty': MailerIsEmptyForm.create(user, item),
            'dont_receive_yet': DontReceiveForm.create(user, item, initial={
                'first_name': order.first_name,
                'last_name': order.last_name,
                'shipping_address1': order.shipping_address1,
                'shipping_address2': order.shipping_address2,
                'shipping_city': order.shipping_city,
                'shipping_state': order.shipping_state,
                'shipping_zip_code': order.shipping_zip_code,
            }),
            'gamemine_not_receive_game': GamemineNotRecieveForm.create(user, item),
        },
    }


@simple_view('claims/trade_claim.html')
def do_trade_claim(request, item):
    user = request.user
    order = item.order
    date_x = (order.create_date or datetime.now()).date()
    less_than_7_days = date_x > (datetime.now().date() - timedelta(7))
    return {
        'shpere': 'Trade',
        'game': item.item,
        'order': order,
        'item': item,
        'less_than_7_days': less_than_7_days,
        'date_x_plus_7': date_x + timedelta(7),
        'forms': {
            'gamemine_not_receive_trade_game': GamemineNotRecieveTradeGameForm.create(user, item),
            'wrong_trade_value_credit': WrongTradeValueCreditForm.create(user, item, initial={'received': '3.44'}),
        },
    }


@simple_view('claims/buy_claim.html')
def do_buy_claim(request, item):
    user = request.user
    order = item.order
    shipping_date = order.get_shipping_date()
    less_than_7_days = shipping_date > (datetime.now().date() - timedelta(7))
    more_than_5_days = shipping_date < (datetime.now().date() - timedelta(5))

    return {
        'shpere': 'Buy',
        'game': item.item,
        'order': order,
        'item': item,
        'less_than_7_days': less_than_7_days,
        'more_than_5_days': more_than_5_days,
        'shipping_date': shipping_date,
        'shipping_date_plus_7': shipping_date + timedelta(7),
        'forms': {
            'game_is_damaged': GameIsDamagedForm.create(user, item),
            'wrong_game': WrongGameForm.create(user, item),
            'dont_receive_yet': DontReceiveForm.create(user, item, initial={
                'first_name': order.first_name,
                'last_name': order.last_name,
                'shipping_address1': order.shipping_address1,
                'shipping_address2': order.shipping_address2,
                'shipping_city': order.shipping_city,
                'shipping_state': order.shipping_state,
                'shipping_zip_code': order.shipping_zip_code,
            })
        },
    }


def get_claim_object(user, sphere, id):
    if sphere == 'Rent':
        return get_object_or_404(RentOrder, user=user, pk=id)
    if sphere == 'Buy':
        return get_object_or_404(BuyOrderItem, order__user=user, pk=id)
    if sphere == 'Trade':
        return get_object_or_404(TradeOrderItem, order__user=user, pk=id)
    raise Exception('Unsupported claim sphere: %s' % sphere)


@login_required
@transaction.commit_on_success
def post_claim(request, sphere, id, claim):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    obj = get_claim_object(request.user, sphere, id)
    ClaimForm = CLAIM_FORMS[claim]
    claim = ClaimForm.Meta.model.get(request.user, obj)
    if claim:
        return redirect('members:report_claim', sphere, id)

    form = ClaimForm(request.POST, instance=claim)
    if not form.is_valid():
        return HttpResponseBadRequest()
    claim = form.save(commit=False)
    claim.claim_object = obj
    claim.user = request.user
    claim.sphere_of_claim = SPHERE_REVERSED_DICT[sphere]
    claim.save()
    if claim.sphere_of_claim == SphereChoice.Rent:
        rent_order = claim.claim_object

        if rent_order.status == RentOrderStatus.Returned:
            claim.delete()
            return redirect('members:report_claim', sphere, id)

        p = rent_order.user.get_profile()
        if claim.type == ClaimType.GamemineNotReceiveGame:
            claim.status = CaseStatus.AutoClosed
            claim.save()
            scans = rent_order.incoming_tracking_scans or {}
            if 'I' in scans or 'A' in scans or 'D' in scans:
                rent_order.inventory.status = InventoryStatus.USPSLost
            else:
                if rent_order.status != RentOrderStatus.Claim:
                    p.inc_strikes()
                rent_order.inventory.status = InventoryStatus.Lost
            rent_order.inventory.save()
            rent_order.status = RentOrderStatus.Claim
            rent_order.save()
        elif claim.type == ClaimType.DontRecieve:
            shipped_date = rent_order.date_shipped
            less_than_7_days = (shipped_date or datetime.now()).date() > (datetime.now().date() - timedelta(7))
            if less_than_7_days:
                claim.delete()
                return redirect('members:report_claim', sphere, id)

            claim.status = CaseStatus.AutoClosed
            claim.save()
            scans = rent_order.outgoing_tracking_scans or {}
            if 'I' in scans or 'A' in scans or 'D' in scans or '-1' in scans:
                if rent_order.status != RentOrderStatus.Claim:
                    p.inc_strikes()
                rent_order.inventory.status = InventoryStatus.Lost
            else:
                rent_order.inventory.status = InventoryStatus.USPSLost
            rent_order.inventory.save()
            rent_order.status = RentOrderStatus.Claim
            rent_order.save()
        elif claim.type in [ClaimType.WrongGame, ClaimType.GameIsDamaged]:
            claim.status = CaseStatus.AutoClosed
            claim.save()
            if rent_order.status != RentOrderStatus.Claim:
                p.inc_strikes()
            rent_order.status = RentOrderStatus.Claim
            rent_order.save()
        else:
            if rent_order.status != RentOrderStatus.Claim:
                p.inc_strikes()
            rent_order.status = RentOrderStatus.Claim
            rent_order.save()

    return redirect('members:report_claim', sphere, id)
