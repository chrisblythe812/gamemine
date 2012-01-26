import logging
import itertools
import sys

from django.core.management.base import LabelCommand
from django.conf import settings
from django.db import transaction

from endiciapy.endicia import Endicia

from project.buy_orders.models import BuyCart, PackSlip, BuyOrderItem,\
    BuyOrderItemStatus, BuyOrder
from project.members.models import BillingHistory, TransactionType,\
    TransactionStatus
from project.inventory.models import Inventory, InventoryStatus, Dropship
from project.catalog.models.items import Item


info = logging.getLogger('crontab').info
error = logging.getLogger('crontab').error
debug = logging.getLogger('crontab').debug
warn = logging.getLogger('crontab').warn


class Command(LabelCommand):
    args = '<purge, update_shipped_statuses, update_order_items, fix_buy_orders, load_inventory>'
    help = 'Working with cart'
    label = 'command'

    def handle_label(self, label, **options):
        getattr(self, 'do_' + label)()

    def do_purge(self):
        BuyCart.purge()

    def do_update_shipped_statuses(self):
        endicia = Endicia(**settings.ENDICIA_CONF)
        debug('Checking mail shipped statuses...')
        for order in PackSlip.objects.exclude(tracking_number=None).filter(date_delivered=None):
            pic = order.tracking_number
            res = endicia.status_request(pic)
            code = res.StatusList.PICNumber.StatusCode
            debug('%s: %s %s', pic, code, res.StatusList.PICNumber.Status)
            order.set_tracking_status(code)

    def do_update_order_items(self):
        def chain_objects(o1, objects=[]):
            return itertools.chain([o1] if o1 else [], itertools.ifilter(lambda x: x != o1, objects))

        def find_dropship(order_item, dropships):
            for dropship in dropships:
                if dropship.is_game_available(order_item.item, order_item.is_new, exclude_buy_order=order_item, for_rent=False):
                    return dropship
            return None

        fl_dropship = Dropship.objects.get(code='FL')
        dropships = [fl_dropship]
        for i in BuyOrderItem.objects.filter(status__in=[BuyOrderItemStatus.Checkout, 
                                                         BuyOrderItemStatus.PreOrder, 
                                                         BuyOrderItemStatus.Pending]).order_by('order__create_date'):
            try:
                if i.item.is_prereleased_game():
                    continue

#                zip_code = i.order.shipping_zip_code
#                profile = i.order.user.get_profile()            
#                dropships = list(chain_objects(profile.dropship, Dropship.list_by_distance(zip_code)))
    
                dc = find_dropship(i, dropships)
                if not dc:
                    i.source_dc = fl_dropship
                    if i.item.is_prereleased_game():
                        i.set_status(BuyOrderItemStatus.PreOrder)
                    else:
                        i.set_status(BuyOrderItemStatus.Checkout)
                    continue

                i.source_dc = dc
                i.set_status(BuyOrderItemStatus.Pending)
            except Exception, _e:
                error('Error occurs when processing buy order %s', i.id, exc_info=sys.exc_info())

    @transaction.commit_on_success
    def do_fix_buy_orders(self):
        for bo in BuyOrder.objects.filter(payment_transaction=None):
            try:
                h = BillingHistory.objects.get(user=bo.user,
                                               type=TransactionType.BuyCheckout, 
                                               status=TransactionStatus.Passed,
                                               description__contains=bo.order_no())
                bo.payment_transaction = h
                bo.save()
            except BillingHistory.DoesNotExist, _e:
                pass

    def do_load_inventory(self):
        import re
        sys.stdin.readline()
        dc = Dropship.objects.get(code='FL')
        s = set()
        no_price = set()
        for l in sys.stdin.readlines():
            barcode = re.search(r'[-A-Z0-9]+', l, re.I).group(0)
            try:
                i = Inventory.objects.get(barcode__regex='^[0]*%s$' % barcode)
                if i.status not in [InventoryStatus.InStock, InventoryStatus.Unknown]:
                    print 'Not in stock:', barcode
                    continue
                if i.item.retail_price_used == 0:
                    no_price.add(i.item.upc) 
                i.status = InventoryStatus.InStock
                i.dropship = dc
                i.is_new = False
                i.buy_only = True
                i.save()
                s.add(i.item.id)
            except Inventory.DoesNotExist:
                print 'Not Found:', barcode
        print len(s)
        for upc in no_price:
            item = Item.objects.get(upc=upc)
            print '\t'.join([item.upc, item.short_name, item.category.name])
