from logging import debug #@UnusedImport
import operator
from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template.context import RequestContext
from django import forms
from django.db.models.query_utils import Q

from django_snippets.views import simple_view
from django_snippets.models.decorators import rollback_on_error

from project.trade.models import TradeOrder, TradeOrderItem
from project.staff.views import staff_only
from project.staff.forms import TradeGameForm
from project.inventory.models import Inventory, Dropship, InventoryStatus
from project.members.models import BillingHistory, TransactionStatus,\
    TransactionType
from project.catalog.models.items import Item
from project.claims.models import Claim, SphereChoice, ClaimType
from project.crm.models import CaseStatus, CASE_STATUSES_PUBLIC


def orders(request, **kwargs):
    message = ''

    latest_processed_items = TradeOrderItem.objects.filter(processed=True).exclude(processed_date=None).order_by('-processed_date', '-order__received_date', '-order__create_date', '-id').select_related()[:10]
    partially_processed_orders = TradeOrder.objects.extra(where=["exists(select * from trade_tradeorderitem where order_id=trade_tradeorder.id and processed='t')",
                                                                 "exists(select * from trade_tradeorderitem where order_id=trade_tradeorder.id and processed='f')"])
    problems = Claim.objects.filter(sphere_of_claim=SphereChoice.Trade, status__lt=CaseStatus.Closed).order_by('-date')[:10]

    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        if barcode:
            try:
                order = TradeOrder.objects.get(barcode=barcode)
                return redirect('staff:trade_order_details', order.id)
            except TradeOrder.DoesNotExist, e: #@UnusedVariable
                message = 'Order with barcode "<strong>%s</strong>" does not exist.' % barcode

    returns = TradeOrderItem.objects.filter(processed=True, is_mailback=True)

    return {
        'title': 'Trade Orders',
        'latest_processed_items': latest_processed_items,
        'partially_processed_orders': partially_processed_orders,

        'message': message,
        'problems': problems,
        'returns': returns,
    }, None


@staff_only
@simple_view('staff/trade/order_details.html')
def order_details(request, id):
    order = get_object_or_404(TradeOrder, id=id)
    if request.is_ajax():
        return render_to_response('staff/trade/orders/partials/order_details.html', {
                'order': order,
            }, RequestContext(request))
    return {
        'title': 'TRADE ORDER ID: %s' % order.order_no(),
        'order': order,
        'page_class': 'staff-trade-order-details',
    }


@staff_only
@simple_view('staff/trade/order_details_item.html')
@transaction.commit_manually
@rollback_on_error
def order_details_item(request, order_id, item_id):
    order = get_object_or_404(TradeOrder, id=order_id)
    item = get_object_or_404(TradeOrderItem, order__id=order_id, id=item_id)

    if request.method=='POST':
        form = TradeGameForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            item.original_item = item.item
            if item.is_match:
                if item.is_damaged and not item.is_refurblished:
                    item.declined = True
            else:
                if request.POST.get('is_accepted') == 'True':
                    accepted_item = get_object_or_404(Item, id=request.POST.get('accepted_id'))
                    item.item = accepted_item
                    item.hot_trade = False
                    if item.is_complete:
                        item.price = accepted_item.trade_price
                    else:
                        item.price = accepted_item.trade_price_incomplete
                else:
                    item.declined = True
            item.processed = True
            item.processed_date = datetime.now()
            item.processed_by = request.user

            for c in item.claims().filter(type=ClaimType.GamemineNotReceiveTradeGame):
                c.status = CaseStatus.AutoClosed
                c.save()

            if not item.declined:
                inventory = Inventory()
                inventory.item = item.item
                inventory.is_new = False
#                inventory.buy_only = request.POST.get('is_desctination') == 'buy';
                inventory.save()
                item.inventory = inventory

            item.save()

            amount = item.price + item.get_shipping_reimbursements()

            profile = order.user.get_profile()

            if order.items.filter(processed=False).count() == 0:
                hot_trades = 0
                for i in order.items.filter(declined=False, hot_trade=True):
                    if i.item == i.original_item:
                        hot_trades += 1
                if hot_trades >= 3:
                    debug('Add bonus')
                    profile.store_credits += order.bonus or 0
                    profile.bonus_store_credits += order.bonus or 0

            if not item.declined:
                profile.store_credits += amount
                profile.bonus_store_credits += item.get_shipping_reimbursements()

                description = 'Trade game. Order#: %s. UPC: %s' % (order.order_no(), item.item.upc)
                BillingHistory.log(order.user, '', description, credit=amount, reason='trade',
                                   status=TransactionStatus.Passed, type=TransactionType.TradePayment)

            profile.save()

            if item.order.is_processed():
                item.order.send_order_processed()

            transaction.commit()
            return redirect('staff:trade_order_details', order_id)
    else:
        form = TradeGameForm(instance=item)

    transaction.rollback()
    return {
        'title': 'TRADE ORDER ID: %s' % order.order_no(),
        'order': order,
        'item': item,
        'form': form,
        'page_class': 'staff-trade-order-details',
    }


@simple_view('staff/trade/trade_order_assign_item.html')
def trade_order_assign_item(request, order_id, item_id):
    class Form(forms.Form):
        used_for = forms.ChoiceField(choices=(('rent', 'Rent'), ('sale', 'Sale')), widget=forms.RadioSelect(), initial='rent')
        dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), initial=1)

    item = get_object_or_404(TradeOrderItem, order__id=order_id, id=item_id)

    if item.inventory and item.inventory.status == InventoryStatus.Available:
        if request.method == 'POST':
            form = Form(request.POST)
            if form.is_valid():
                if form.cleaned_data['used_for'] == 'sale':
                    item.inventory.buy_only = True
                    item.inventory.dropship = Dropship.objects.get(code='FL')
                    item.inventory.status = InventoryStatus.InStock
                else:
                    item.inventory.buy_only = False
                    item.inventory.dropship = form.cleaned_data['dc']
                item.inventory.fill_barcode()
                item.inventory.save()
            return redirect(request.META['HTTP_REFERER'])
        else:
            form = Form()
    else:
        form = None

    return {
        'item': item,
        'form': form,
    }


def orders__pending_arrival(request, **kwargs):
    orders = TradeOrder.objects.filter(received_date=None).exclude(items__processed=True).order_by('-create_date')
    return {
        'title': 'Rent Orders: Pending Arrival',
        'paged_qs': orders,
    }, None, ('orders', 50)


def orders__processed_items(request, **kwargs):
    class Form(forms.Form):
        status = forms.ChoiceField(choices=(('', '----------'), ('assigned', 'Assigned'), ('unassigned', 'Unassigned'), ), required=False)
        q = forms.CharField(required=False)

    items = TradeOrderItem.objects.filter(processed=True)

    form = Form(request.GET)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            qq = q.split()
            filters = []
            fields = ['order__barcode', 'order__user__first_name', 'order__user__last_name', 'order__user__email', 'item__upc', 'item__short_name', 'item__inventory__barcode']
            for q in qq:
                ff = []
                for f in fields:
                    ff.append(Q(**{f + '__icontains': q}))
                filters.append(reduce(operator.or_, ff))
            items = items.filter(reduce(operator.and_, filters)).distinct('item')
        status = form.cleaned_data.get('status')
        if status:
            if status == 'assigned':
                items = items.exclude(inventory__dropship=None)
            else:
                items = items.filter(inventory__dropship=None)

    items = items.order_by('-processed_date', '-order__received_date', '-order__create_date', '-id').select_related()

    items = list(items.exclude(processed_date=None)) + list(items.filter(processed_date=None))

    return {
        'title': 'Trade: Processed Items',
        'paged_qs': items,
        'form': form,
    }, None, ('items', )


def claims_and_disputes(request, **kwargs):
    class Form(forms.Form):
        status = forms.ChoiceField(choices=[(None, '-----------')] + list(CASE_STATUSES_PUBLIC), required=False)
#        q = forms.CharField(required=False)

    form = Form(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Trade/Claims-and-Disputes')

    claims = Claim.objects.filter(sphere_of_claim=SphereChoice.Trade).order_by('-date')
    status = form.cleaned_data.get('status')
    if status and status != 'None':
        if status == CaseStatus.Closed:
            claims = claims.filter(status__in=[CaseStatus.Closed, CaseStatus.AutoClosed])
        else:
            claims = claims.filter(status=status)
#    q = form.cleaned_data.get('q')
#    if q:
#        claims = search(claims, q, ['user__first_name', 'user__last_name'])

    return {
        'title': 'Trade: Claims / Disputes',
        'paged_qs': claims,
        'form': form,
    }, None, ('claims', 50)
