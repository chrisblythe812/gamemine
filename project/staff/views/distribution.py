import datetime
from django.shortcuts import redirect, get_object_or_404
from django.db import connection
from project.catalog.models import Item, Category
from project.rent.models import RentOrderStatus
from project.inventory.models import Purchase, PurchaseItem, Distributor
from project.staff.forms import DCManagementSearchForm, PurchaseForm, PurchaseItemFormSet, DCSelectForm
from project.buy_orders.models import BuyOrderItemStatus

def get_stat(status, date_field, date_from, date_to):
    q = '''select catalog_item.category_id, count(1)
        from rent_rentorder
        join catalog_item on rent_rentorder.item_id = catalog_item.id
        where rent_rentorder.status = %d''' % status
    if date_from:
        q += ' and "%s" >= \'%s\'' % (date_field, date_from) 
    if date_to:
        q += ' and "%s" <= \'%s\'' % (date_field, date_to) 
    q += ' group by catalog_item.category_id'

    cursor = connection.cursor() #@UndefinedVariable
    cursor.execute(q)
    result = {}
    for row in cursor.fetchall():
        result[row[0]] = row[1]
    return result


def management(request, **kwargs):
    form = DCManagementSearchForm(request.GET)
    date_from, date_to = form.get_data()

    shipped = get_stat(RentOrderStatus.Shipped, 'date_shipped', date_from, date_to)
    received = get_stat(RentOrderStatus.Returned, 'date_returned', date_from, date_to)

    categories = Category.objects.all()

    shipped_total = 0
    received_total = 0
    for category in categories:
        category.shipped = shipped.get(category.id, 0)
        category.received = received.get(category.id, 0)

        category.total = category.shipped + category.received
        shipped_total += category.shipped
        received_total += category.received

    return {
        'title': 'DC Management',
        'form': form,
        'stat': categories,
        'shipped_total': shipped_total, 
        'received_total': received_total,
        'total': shipped_total + received_total,
    }, None


def operations(request, **kwargs):
    dcform, dc = DCSelectForm.get_dc(request)
    categories = Category.objects.all()

    cursor = connection.cursor() #@UndefinedVariable

    q = '''
    select count(o.id) from buy_orders_buyorderitem oi 
        inner join buy_orders_buyorder o on oi.order_id=o.id
    where 
        oi.status in (0,1,2,3) and
        oi.source_dc_id=%d
    ''' % dc.id
    cursor.execute(q)
    ca_buy_orders =  cursor.fetchall()[0][0]

    q = '''
    select count(*) from (select distinct oi.item_id from buy_orders_buyorderitem oi 
        inner join buy_orders_buyorder o on oi.order_id=o.id
    where 
        oi.status in (0,1,2,3) and
        oi.source_dc_id=%d) as xxx;
    ''' % dc.id
    cursor.execute(q)
    ca_buy_titles =  cursor.fetchall()[0][0]

    q = '''
    select count(oi.id) from buy_orders_buyorderitem oi 
        inner join buy_orders_buyorder o on oi.order_id=o.id
    where 
        oi.status in (0,1,2,3) and
        oi.source_dc_id=%d
    ''' % dc.id
    cursor.execute(q)
    ca_buy_pick =  cursor.fetchall()[0][0]


    #####################################################################

    q = '''select count(id) from rent_rentorder where status=0 and source_dc_id=%d''' % dc.id
    cursor.execute(q)
    ca_rent_orders =  cursor.fetchall()[0][0]

    q = '''
    select count(*) from (select distinct item_id from rent_rentorder where status=0 and source_dc_id=%d) as xxx;
    ''' % dc.id
    cursor.execute(q)
    ca_rent_titles =  cursor.fetchall()[0][0]

    current_allocation = [
        {'website':'Buy', 'orders':ca_buy_orders, 'transfers':'N/A', 'titles':ca_buy_titles, 'pick':ca_buy_pick},
        {'website':'Rent', 'orders':ca_rent_orders, 'transfers':'N/A', 'titles':ca_rent_titles, 'pick':ca_rent_orders},
    ]

    #####################################################################

    buy_statistics = []
    for c in categories:
        cursor.execute("select count(oi.id) from buy_orders_buyorderitem oi inner join catalog_item i on oi.item_id=i.id where oi.source_dc_id=%d and i.category_id=%d and oi.status=%d" % (dc.id, c.id, BuyOrderItemStatus.Shipped))
        approved = cursor.fetchall()[0][0]
        cursor.execute("select count(oi.id) from buy_orders_buyorderitem oi inner join catalog_item i on oi.item_id=i.id where oi.source_dc_id=%d and i.category_id=%d and oi.status in (%d, %d, %d, %d)" % (dc.id, c.id, BuyOrderItemStatus.Canceled, BuyOrderItemStatus.AutoCancel, BuyOrderItemStatus.Refund, BuyOrderItemStatus.Chargeback))
        declined = cursor.fetchall()[0][0]
        buy_statistics.append({'platform':c.name,'approved':approved, 'declined':declined})

    rent_statistics = []
    for c in categories:
        cursor.execute("select count(oi.id) from rent_rentorder oi inner join catalog_item i on oi.item_id=i.id where oi.source_dc_id=%d and i.category_id=%d and oi.status=%d" % (dc.id, c.id, 1))
        shipped = cursor.fetchall()[0][0]
        cursor.execute("select count(oi.id) from rent_rentorder oi inner join catalog_item i on oi.item_id=i.id where oi.source_dc_id=%d and i.category_id=%d and oi.status=%d" % (dc.id, c.id, 2))
        returned = cursor.fetchall()[0][0]
        rent_statistics.append({'platform':c.name,'shipped':shipped, 'returned':returned})

    return {
        'title': 'DC Operations',
        'dcform': dcform,
        'dc': dc,
        'current_allocation': current_allocation,
        'buy_statistics': buy_statistics,
        'rent_statistics': rent_statistics,
    }, None


def purchases(request, **kwargs):
    return {
        'title': 'Purchases',
        'purchases': Purchase.objects.all(),
    }, None


def create_purchase(request, **kwargs):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        formset = PurchaseItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            purchase = Purchase()
            purchase.distributor = get_object_or_404(Distributor, id=form.cleaned_data['distributor'])
            purchase.created = datetime.datetime.now()
            purchase.status = 0
            purchase.is_new = form.cleaned_data['is_new']
            purchase.save() 
            for f in formset.forms:
                item = PurchaseItem()
                item.purchase = purchase
                item.item = get_object_or_404(Item, upc=f.cleaned_data['upc'])
                item.quantity = f.cleaned_data['quantity']
                item.save()
            return redirect('staff:page', 'Distribution/Purchases'), None
    else:
        form = PurchaseForm()
        formset = PurchaseItemFormSet()
    return {
        'title': 'Create Purchase',
        'form': form,
        'formset': formset,
    }, None
