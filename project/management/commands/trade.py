import datetime
from logging import debug #@UnusedImport

from django.core.management.base import LabelCommand
from django.contrib.contenttypes.models import ContentType

from project.trade.models import TradeOrder, TradeOrderItem
from project.claims.models import GamemineNotRecieveTradeGameClaim
from project.crm.models import CaseStatus
from project.mailer.models import Letter


class Command(LabelCommand):
    args = '[fix]'
    help = 'Working with cart'
    label = 'command'

    def handle_label(self, label, **options):
        getattr(self, 'do_' + label)()

    def do_fix(self):
        for item in TradeOrderItem.objects.filter(processed=True):
            ct = ContentType.objects.get_for_model(item)
            for c in GamemineNotRecieveTradeGameClaim.objects.filter(content_type__pk=ct.id, object_id=item.id):
                c.status = CaseStatus.AutoClosed
                c.save()

    def do_notify_cancelled_expired(self):
        ten_days_earlier = datetime.datetime.now() - datetime.timedelta(10)
        orders = TradeOrder.objects.filter(create_date__lte=ten_days_earlier)
        for order in orders:
            order.send_order_expired()

#    def do_fix_inventory(self):
#        for i in TradeOrderItem.objects.filter(id__in=[22, 44, 102, 97, 56, 83, 109, 122]):
#            i.inventory = None
#            i.save()
#            
#        for i in TradeOrderItem.objects.filter(processed=True, inventory=None):
#            inventories = Inventory.objects.filter(dropship=None, item=i.item, is_new=False, trade_item=None)
#            if not inventories:
#                continue
#            inventory = inventories[0]
#            i.inventory = inventory
#            i.save() 
#        
#        
#        for i in TradeOrderItem.objects.filter(inventory__id__in=[10744, 11587, 11588, 11194, 11200, 11201, 11196]):
#            for ii in list(i.inventory.trade_item.all())[:-1]:
#                ii.inventory = None
#                ii.save()
#        for i in TradeOrderItem.objects.filter(processed=True, inventory=None):
#            inventories = Inventory.objects.filter(dropship=None, item=i.item, is_new=False, trade_item=None)
#            if not inventories:
#                continue
#            inventory = inventories[0]
#            i.inventory = inventory
#            i.save() 

    def do_fix_dates(self):
        for i in TradeOrderItem.objects.filter(processed_date=None, processed=True):
            order = i.order
            try:
                letter = Letter.objects.get(subject__icontains='#%s Processed' % order.order_no())
                i.processed_date = letter.created
                i.bastard_flag = True
                i.save()
                print i.processed_date
            except Letter.DoesNotExist:
                print '!!!!!!!!!!!!!!'
