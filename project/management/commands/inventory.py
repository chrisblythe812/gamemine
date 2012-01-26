from logging import debug
import random
import decimal

from django.core.management.base import LabelCommand
from django.db import transaction

from project.catalog.models.items import Item
from project.inventory.models import Dropship, Inventory, InventoryStatus
from project.rent.models import RentOrder, RentOrderStatus


class Command(LabelCommand):
    args = '[testdata]'
    help = 'Working with cart'
    label = 'command'

    def handle_label(self, label, **options):
        getattr(self, 'do_' + label)()

    @transaction.commit_on_success
    def do_testdata(self):
        random.seed()
        
        dropships = list(Dropship.objects.all())
        for item in Item.objects.all():
            if not random.choice([True, True, False]):
                debug('Skip %s...', item)
                continue
            debug('Creating inventory for %s...', item)
            for x in xrange(2): #@UnusedVariable
                dropship = random.choice(dropships)
                x = random.randint(0, 10)
                debug('    add %d items to %s...', x, dropship)
                for xx in xrange(x): #@UnusedVariable
                    i = Inventory(dropship=dropship,
                                  item=item,
                                  is_new=random.choice([True, False]),
                                  status=random.choice([InventoryStatus.InStock, InventoryStatus.Available, InventoryStatus.Rented]))
                    price = decimal.Decimal('%f' % random.uniform(0.3, 1))
                    if i.is_new:
                        item.retail_price_new = price
                    else:
                        item.retail_price_used = price
                    item.save()
                    i.fill_barcode()
                    i.save()

        debug('Updating rent_flag...')
        for item in Item.objects.all():
            item.rent_flag = item.available_for_selling()
            item.save()
            
    def do_fix(self):
        for o in RentOrder.objects.filter(status=RentOrderStatus.Shipped):
            if o.inventory and o.inventory.status != InventoryStatus.Rented:
                o.inventory.status = InventoryStatus.Rented
                o.inventory.save()
            