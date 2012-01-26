import operator
from logging import debug #@UnusedImport
from datetime import datetime

from django.db.models import Count
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template.context import RequestContext
from django.db import transaction
from django.forms.models import modelformset_factory, ModelForm
from django import forms
from django.db.models.query_utils import Q

from django_snippets.views import simple_view

from project.buy_orders.models import BuyOrderItem, BuyOrderItemStatus, PackSlip,\
    BuyOrder
from project.catalog.models.items import Item
from project.staff.views import ajax_only, staff_only
from project.inventory.models import Dropship, Inventory, InventoryStatus,\
    DistributorItem
from project.catalog.models.categories import Category
from django_snippets.views.json_response import JsonResponse


@transaction.commit_on_success
def orders(request, **kwargs):
    message = ''
    
    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        if barcode:
            try:
                inventory = Inventory.objects.get(barcode=barcode, status=InventoryStatus.InStock, buy_only=True)
                order_item = BuyOrderItem.objects.filter(status=BuyOrderItemStatus.Pending, 
                                                         source_dc=inventory.dropship,
                                                         is_new=inventory.is_new,
                                                         item=inventory.item).order_by('order__create_date')
                if order_item.count():
                    order_item = order_item[0]
                    slip_item = PackSlip.prepare_order_item(order_item)
                    slip_item.order_item.inventory = inventory
                    slip_item.order_item.status = BuyOrderItemStatus.Prepared 
                    slip_item.order_item.date_prepared = datetime.now()
                    slip_item.order_item.save()
                    inventory.status = InventoryStatus.Pending
                    inventory.save()
                    message = 'Barcode "<strong>%s</strong>" was successfully added to the Prepared List.' % barcode
                else:
                    message = 'Barcode "<strong>%s</strong>" does not match any item in Picked List.' % barcode
            except Inventory.DoesNotExist, e: #@UnusedVariable
                message = 'Barcode "<strong>%s</strong>" does not exist or it does not in stock.' % barcode

    picked_list = BuyOrderItem.objects.filter(status__in=[BuyOrderItemStatus.Pending])
    
    if not request.user.is_superuser:
        p = request.user.get_profile()
        if p.dc:
            picked_list = picked_list.filter(source_dc=p.dc)
    
    picked_list = picked_list.values('item', 'source_dc', 'is_new').annotate(quantity=Count('item')).order_by('item__category', 'item')
    all_picked_games = reduce(lambda a, b: a + b['quantity'], picked_list, 0)
    
    picked_list = map(lambda x: {
        'item': Item.objects.get(id=x['item']),
        'is_new': x['is_new'], 
        'dropship': Dropship.objects.get(id=x['source_dc']) if x['source_dc'] else None, 
        'quantity': x['quantity']
    }, picked_list)

    prepared_list = PackSlip.objects.filter(date_shipped=None).order_by('-created')
    prepared_list_ids = map(lambda x: x.id, prepared_list)  

    return {
        'title': 'Buy Orders',
        'message': message,
        'picked_list': picked_list,
        'all_picked_games': all_picked_games,
        'prepared_list': prepared_list,
        'prepared_list_ids': prepared_list_ids,
    }, None


class ItemDescriptor(object):
    def __init__(self, id, is_new):
        self.id = id
        self.is_new = is_new
        self._item = None
        
    def get_item(self):
        if not self._item:
            self._item = Item.objects.get(id=self.id)
        return self._item
    
    def get_amount_instock_to_buy(self):
        return self.get_item().get_amount_instock_to_buy(self.is_new)
    
    def get_amount_from_distributor_to_buy(self):
        return self.get_item().get_amount_from_distributor_to_buy(self.is_new)


def orders__pre_ordered(request, **kwargs):
#    orders = []
#    for o in BuyOrderItem.objects.order_by('item__short_name').filter(status__in=[BuyOrderItemStatus.PreOrder]).values('item', 'is_new').annotate(Count('item')):
#        orders.append({
#            'item': ItemDescriptor(o['item'], o['is_new']),
#            'count': o['item__count'], 
#            'is_new': o['is_new'],
#        })
    orders = BuyOrderItem.objects.filter(status__in=[BuyOrderItemStatus.PreOrder]).order_by('-order__create_date')
    return {
        'title': 'Buy Orders: Pre-Ordered',
        'paged_qs': orders,
    }, None, ('orders', )


def orders__not_in_stock(request, **kwargs):
#    orders = []
#    for o in BuyOrderItem.objects.order_by('item__short_name').filter(status__in=[BuyOrderItemStatus.Checkout]).values('item', 'is_new').annotate(Count('item')):
#        orders.append({
#            'item': ItemDescriptor(o['item'], o['is_new']),
#            'count': o['item__count'], 
#            'is_new': o['is_new'],
#        })
    orders = BuyOrderItem.objects.filter(status__in=[BuyOrderItemStatus.Checkout]).order_by('-order__create_date')
    return {
        'title': 'Buy Orders: Not in Stock',
        'paged_qs': orders,
    }, None, ('orders', )


@staff_only
@ajax_only
def buy_orders_not_in_stock_details(request, item_id, condition):
    item = get_object_or_404(Item, id=item_id)
    
    order_items = BuyOrderItem.objects.filter(status=BuyOrderItemStatus.Checkout, item=item, is_new=condition=='NG').order_by('-order__create_date')
    
    return render_to_response('staff/buy/orders/partials/orders_details.html', {
            'item': item,
            'order_items': order_items,
        }, RequestContext(request))


@staff_only
@ajax_only
def buy_orders_pre_ordered_details(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    
    order_items = BuyOrderItem.objects.filter(status=BuyOrderItemStatus.PreOrder, item=item)
    
    return render_to_response('staff/buy/orders/partials/orders_details.html', {
            'item': item,
            'order_items': order_items,
        }, RequestContext(request))


@staff_only
@ajax_only
def buy_pick_list_details(request, item_id, dc):
    item = get_object_or_404(Item, id=item_id)
    dc = get_object_or_404(Dropship, id=dc)
    
    order_items = BuyOrderItem.objects.filter(status=BuyOrderItemStatus.Pending, source_dc=dc, item=item)
    
    return render_to_response('staff/buy/orders/partials/buy_pick_list_details.html', {
            'item': item,
            'order_items': order_items,
        }, RequestContext(request))


def orders__shipped(request, **kwargs):
    pack_slips = PackSlip.objects.exclude(date_shipped=None).order_by('-date_shipped')

#    if not request.user.is_superuser:
#        p = request.user.get_profile()
#        pack_slips = pack_slips.filter(source_dc=p.dc)
    
    return {
        'title': 'Buy Orders: Shipped',
        'paged_qs': pack_slips,
    }, None, ('pack_slips', )


def orders__returns(request, **kwargs):
    return {
        'title': 'Buy Orders: Returns',
    }, None


@staff_only
@transaction.commit_on_success
def mark_shipped(request):
    ids = request.REQUEST.get('ids', '')
    for id in ids.split(','):
        if not id:
            continue
        PackSlip.objects.get(id=int(id)).mark_as_shipped()
    return redirect('staff:page', 'Buy/Orders')


def game_weight_matrix(request, **kwargs):
    class CategoryForm(ModelForm):
        class Meta:
            model = Category
            fields = ['game_weight']
    
    CategoryFormSet = modelformset_factory(Category, form=CategoryForm, extra=0)
    if request.method == "POST":
        formset = CategoryFormSet(request.POST, queryset=Category.objects.filter(active=True))
        if formset.is_valid():
            formset.save()
    else:
        formset = CategoryFormSet(queryset=Category.objects.filter(active=True))
    return {
        'title': 'Game Weight Matrix',
        'formset': formset,
    }, None


@staff_only
@simple_view('staff/buy/orders/details.html')
def buy_order_details(request, order_id):
    buy_order = get_object_or_404(BuyOrder, pk=order_id)
    
    if request.is_ajax() and 'action' in request.REQUEST:
        action = request.REQUEST['action']
        if action == 'cancel':
            buy_order.cancel_order()
        return JsonResponse({'status': 'ok'})
    
#    packslip = get_object_or_404(PackSlip, pk=order_id)
    return {
        'title': 'Buy Order Details',
        'order': buy_order,
        'page_class': 'staff-page-buy-order-details',
    }
    
    
def ingram(request, **kwargs):
    class FilterForm(forms.Form):
        q = forms.CharField(required=False, label='')
        platform = forms.ModelChoiceField(queryset=Category.list(), required=False)

    qs = DistributorItem.objects.filter(distributor__id=5).select_related().order_by('item__short_name')

    form = FilterForm(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Buy/Ingram')

    platform = form.cleaned_data.get('platform')
    if platform:
        qs = qs.filter(item__category=platform)
    
    q = form.cleaned_data.get('q')
    if q:
        or_q = []
        for f in ['item__upc', 'item__name', 'item__short_name']:
            or_q.append(Q(**{f + '__icontains': q}))
        qs = qs.filter(reduce(operator.or_, or_q))
    
    return {
        'title': 'Buy: Ingram',
        'form': form,
        'paged_qs': qs,
    }, None, ('items', 50)
