from logging import debug #@UnusedImport
import decimal

from django.db import models
from django.conf import settings
import itertools


PURCHASE_STATUS_CHOICES = (
    (0, u'New'),
    (1, u'In Progress'),
    (2, u'Declined'),
    (3, u'Shipped'),
    (4, u'Completed'),
)


class Distributor(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    new_games_vendor = models.BooleanField(default=True)

    @staticmethod
    def choices():
        return [(d.id, d.name) for d in Distributor.objects.all()]
        
    def __unicode__(self):
        return self.name


class DistributorItem(models.Model):
    distributor = models.ForeignKey(Distributor, related_name='items')
    item = models.ForeignKey('catalog.item')

    is_new = models.BooleanField(default=True, db_index=True)

    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=decimal.Decimal('0.0'))
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=decimal.Decimal('0.0'))
    quantity = models.IntegerField(null=True, blank=True)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))

    retail_price_used_vendor = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    wholesale_price_used = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    quantity_used = models.IntegerField(default=0)

    trade_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    trade_price_incomplete = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    
#    class Meta:
#        app_label = 'inventory'
#        unique_together = (('distributor', 'item'),)


class Dropship(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=2)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    postal_code = models.CharField(max_length=10)
    bid = models.CharField(max_length=50)
    lat = models.FloatField(null=True)
    lon = models.FloatField(null=True)

    printers = models.CharField(max_length=255, blank=True, null=True)
    label_sizes = models.CharField(max_length=255, blank=True, null=True)
    
    enable_for_rent = models.BooleanField(default=True)
        
    @staticmethod
    def find_closest(zip):
        if settings.MELISSA:
            return Dropship.list_by_distance(zip)[0]
        else:
            return Dropship.objects.all()[0]

    @staticmethod
    def list_by_distance(zip):
        melissa = settings.MELISSA
        if not melissa:
            return Dropship.objects.all()
        
        zip_coords = melissa.get_coords_by_zip_code(zip)
        res = []
        for dc in Dropship.objects.all():
            res.append((melissa.compute_distance(zip_coords, (dc.lat, dc.lon)), dc))
        res.sort(lambda x, y: cmp(x[0], y[0]))
        return map(lambda x: x[1], res)
    
    def is_game_available(self, item, is_new=None, exclude_rent_order=None, exclude_buy_order=None, for_rent=True):
        from project.rent.models import RentOrder, RentOrderStatus
        from project.buy_orders.models import BuyOrderItem, BuyOrderItemStatus 
        
        if for_rent and not self.enable_for_rent:
            return False

        qs = Inventory.objects.filter(item=item, dropship=self, status=InventoryStatus.InStock)
        if is_new is not None:
            qs = qs.filter(is_new=is_new)
        if for_rent:
            qs = qs.exclude(buy_only=True)
        else:
            qs = qs.filter(buy_only=True)
        available_amount = qs.count()
        
        if for_rent:
            r1 = RentOrder.objects.filter(item=item, source_dc=self, status=RentOrderStatus.Pending)
            if exclude_rent_order:
                r1 = r1.exclude(id=exclude_rent_order.id)
            r1 = r1.count()
            r2 = 0
        else:
            r2 = BuyOrderItem.objects.filter(item=item, source_dc=self, status=BuyOrderItemStatus.Pending)
            if exclude_buy_order:
                r2 = r2.exclude(id=exclude_buy_order.id)
            r2 = r2.count()
            r1 = 0

        reserved_amount = r1 + r2
        return available_amount - reserved_amount > 0
    
    def __unicode__(self):
        return self.name 
    
    @staticmethod
    def choices(with_all=False):
        ch = [(d.id, d.code) for d in Dropship.objects.all()]
        if with_all:
            ch = [(0, 'ALL')] + ch
        return ch

    @staticmethod
    def find_closest_dc(zip_code, item, home_dc=None, for_rent=True):
        def chain_objects(o1, objects=[]):
            return itertools.chain([o1] if o1 else [], itertools.ifilter(lambda x: x != o1, objects))

        for dropship in list(chain_objects(home_dc, Dropship.list_by_distance(zip_code))):
            if dropship.is_game_available(item, for_rent=for_rent):
                return dropship
        return None


class Purchase(models.Model):
    created = models.DateTimeField(db_index=True)
    status = models.IntegerField(db_index=True, choices=PURCHASE_STATUS_CHOICES)
    distributor = models.ForeignKey(Distributor)
    is_new = models.BooleanField()


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, db_index=True, related_name='items')
    item = models.ForeignKey('catalog.item', db_index=True)
    quantity = models.IntegerField()

    def get_distributor_item(self):
        items = DistributorItem.objects.filter(distributor=self.purchase.distributor, item=self.item)
        if items.count():
            return items[0]
        else:
            return None
    
    def price(self):
        item = self.get_distributor_item()
        if item:
            return item.wholesale_price
        else:
            return None

    def total(self):
        item = self.get_distributor_item()
        if item and item.quantity >= self.quantity:
            return item.wholesale_price * self.quantity
        else:
            return None

    class Meta:
        app_label = 'inventory'


class InventoryStatus:
    Available = 0
    Rented = 1
    Pending = 2
    InStock = 3
    Sold = 4
    Sale = 5
    Damaged = 6
    Lost = 7
    Unknown = 8
    Unreconciled = 9
    AutoUnknown = 10
    USPSLost = 11


INVENTORY_STATUSES = (
    (InventoryStatus.Available, 'Available'),
    (InventoryStatus.Rented, 'Rented'),
    (InventoryStatus.Pending, 'Pending'),
    (InventoryStatus.InStock, 'In Stock'),
    (InventoryStatus.Sold, 'Sold'),
    (InventoryStatus.Sale, 'Unreturned'),
    (InventoryStatus.Damaged, 'Damaged'),
    (InventoryStatus.Lost, 'Lost'),
    (InventoryStatus.Unknown, 'Unknown'),
    (InventoryStatus.Unreconciled, 'Unreconciled'),
    (InventoryStatus.AutoUnknown, 'AutoUnknown'),
    (InventoryStatus.USPSLost, 'USPS (L)'),
)

INVENTORY_STATUS_STR = (
    (-1, 'Unassigned'),
    (InventoryStatus.Available, 'Assigned'),
    (InventoryStatus.InStock, 'In Stock'),
    (InventoryStatus.Pending, 'Prepared'),
    (InventoryStatus.Rented, 'Rented'),
    (101, 'Unreturned'),
    (InventoryStatus.Sold, 'Sold'),
    (InventoryStatus.Damaged, 'Damaged'),
    (InventoryStatus.Lost, 'Lost'),
    (InventoryStatus.Unknown, 'Unknown'),
    (InventoryStatus.Unreconciled, 'Unreconciled'),
    (InventoryStatus.AutoUnknown, 'Unknown'),
    (InventoryStatus.USPSLost, 'USPS (L)'),
)
INVENTORY_STATUS_STR_DICT = dict(INVENTORY_STATUS_STR)

def str_pad_left(s, length):
    s = str(s)
    return '0' * (length - len(s)) + s

class Inventory(models.Model):
    dropship = models.ForeignKey(Dropship, null=True, blank=True, db_index=True)
    item = models.ForeignKey('catalog.item', null=True, db_index=True)
    purchase_item = models.ForeignKey(PurchaseItem, db_index=True, null=True, blank=True)
    barcode = models.CharField(max_length=100, null=True, blank=True, unique=True)
    is_new = models.BooleanField(db_index=True)
    status = models.IntegerField(choices=INVENTORY_STATUSES, db_index=True, default=InventoryStatus.Available)
    not_expected_to_return = models.BooleanField(default=False)
    manual_checked = models.BooleanField(default=False, verbose_name='Manually checked')
    added_at_manual_check = models.BooleanField(default=False)
    manual_checked_dc = models.ForeignKey(Dropship, null=True, related_name='manual_checked')
    manual_check_discarded = models.BooleanField(default=False, verbose_name='Manually checked')
    
    tmp_saved_dc_code = models.CharField(max_length=2, null=True)
    tmp_new_dc_code_aproved = models.NullBooleanField()
    
    buy_only = models.NullBooleanField(db_index=True)
    
    class Meta:
        verbose_name_plural = 'Inventories'

    def fill_barcode(self):
        if self.barcode or not self.dropship:
            return
        
        c = 0
        for i in Inventory.objects.filter(item=self.item, dropship=self.dropship):
            if len(i.barcode or '') != 15:
                continue
            c = max(c, int(i.barcode[5:-6].lstrip('0')))
        if c == 0:
            c = Inventory.objects.filter(item=self.item, dropship=self.dropship).count()
        while True:
            c += 1 
            bc = str_pad_left(self.dropship.bid, 3) + str_pad_left(self.item.category.bid, 2) + str_pad_left(c, 4) + str_pad_left(self.item.id, 6)
            try:
                Inventory.objects.get(barcode=bc)
            except:
                break
        
        self.barcode = bc
        debug('New barcode: %s', self.barcode)
        
    def get_status_str(self):
        if self.status == InventoryStatus.Available:
            return 'Assigned' if self.dropship else 'Unassigned'
        if self.status in [InventoryStatus.AutoUnknown, InventoryStatus.Sale]:
            return 'Unreturned' 
        return INVENTORY_STATUS_STR_DICT[self.status]
        

    def __unicode__(self):
        return u'%s %s (%s) %s' % ('NG' if self.is_new else 'UG', self.item, self.dropship, self.get_status_display()) 

    def manual_check(self, dc, is_new=None, save=True):
        from project.rent.models import RentOrder, RentOrderStatus
        
        self.dropship = dc
        self.not_expected_to_return = False
        if is_new is not None:
            self.is_new = is_new
        self.status = InventoryStatus.InStock
        self.manual_checked = True
        for o in RentOrder.objects.filter(status=RentOrderStatus.Shipped, inventory=self):
            o.status=RentOrderStatus.AutoCanceledByManualCheck
            o.save()
        if save:
            self.save()
        return self
    
    @staticmethod
    def find_by_barcode(barcode):
        for i in Inventory.objects.filter(barcode__iexact=barcode):
            return i
        return None
    
    def mark_as_unreconciled(self):
        from project.rent.models import RentOrder, RentOrderStatus
        
        self.status = InventoryStatus.Unreconciled
        self.save()
        for o in RentOrder.objects.filter(status=RentOrderStatus.Shipped, inventory=self):
            o.status=RentOrderStatus.AutoCanceledByManualCheck
            o.save()
        