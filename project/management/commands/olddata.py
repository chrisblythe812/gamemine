import sys
import MySQLdb
from datetime import datetime
import decimal

from django.core.management.base import LabelCommand
from django.conf import settings

from melissadata.errors import MelissaAddressError, MelissaNameError

from project.catalog.models.items import Item
from project.catalog.models.categories import Category
from project.rent.models import RentOrder, RentOrderStatus, MemberRentalPlan,\
    RentalPlanStatus, RentalPlan
from project.inventory.models import InventoryStatus
from project.members.models import BillingHistory, BillingCard, Profile,\
    TransactionStatus, TransactionType
from django.contrib.auth.models import User


DROPSHIP_MAP = {
    1: 2, # NJ
    2: 1, # FL
    3: 3, # NV
}

CATEGORY_MAP = {
    1: 3,
    2: 1,
    3: 6,
    4: 5,
    5: 7,
    6: 4,
    7: 2,
    8: 8,
    12: 12,
}

INVENTORY_STATUS_MAP = {
    1: InventoryStatus.InStock, # Available
    2: InventoryStatus.Rented, # Rented
    3: InventoryStatus.Sold, # Sold
    4: InventoryStatus.Damaged, # Damaged
    5: InventoryStatus.Pending, # Invoiced
    6: InventoryStatus.Lost, # Lost
    7: InventoryStatus.Sale, # Left to canceled member
}

class Command(LabelCommand):
    def _get_args(self):
        for m in dir(self):
            if m.startswith('do_'):
                yield m[3:]
    
    help = 'Working with old data "ORDZINIKIDZE 10!"'
    label = 'command'

    def handle_label(self, label, **options):
        try:
            method = getattr(self, 'do_' + label)
        except:
            print >>sys.stderr, 'Possible commands: %s' % ', '.join(self._get_args())
            return
        self._items_cache = {}
        self._missing_items = set()
        method()

    def _get_cursor(self):
        if not hasattr(self, 'mconn'):
            self.mconn = MySQLdb.connect(host='78.31.177.17', db="gamemine", user='gamemine', passwd='1')
        return self.mconn.cursor()
    
    
    def get_item(self, upc, category_id=None):
        if upc in self._items_cache:
            return self._items_cache[upc]
        try:
            filter = {'upc__icontains': upc, }
            category_id = CATEGORY_MAP.get(int(category_id or '0'))
            if category_id:
                filter['category'] = Category.objects.get(pk=category_id)
            item = Item.objects.get(**filter)
        except Item.DoesNotExist:
            self._missing_items.add(upc)
            item = None 
        self._items_cache[upc] = item
        return item


    def do_fix_inventory(self):
        from project.inventory.models import Inventory
        statuses = {
            1: InventoryStatus.InStock, # Available
            2: InventoryStatus.Rented, # Rented
            3: InventoryStatus.Sold, # Sold
            4: InventoryStatus.Damaged, # Damaged
            5: InventoryStatus.Pending, # Invoiced
            6: InventoryStatus.Lost, # Lost
            7: InventoryStatus.Sale, # Left to canceled member
        }

        cursor = self._get_cursor()
        cursor.execute('''
        select i.upc, i.id item_id, i.ref_category, s.id `status`, c.name `condition`, e.code, e.ref_center, e.id
            from entries e 
                inner join items i on i.id = e.ref_item
                left outer join entry_statuses s on s.id = e.ref_entry_status
                left outer join entry_conditions c on c.id = e.ref_entry_condition
        ''')
        new_inventory_count = 0
        for upc, id, category_id, status, condition, barcode, ref_center, _entry_id in cursor.fetchall():
            if not upc:
                continue
            item = self.get_item(upc, category_id)
            if not item:
                print 'UPC %s not found' % upc 
                continue
            o, created = Inventory.objects.get_or_create(
                item=item,
                barcode=barcode,
            ) 
            o.dropship_id = DROPSHIP_MAP[ref_center]
            o.is_new = condition == 'New'
            o.status = statuses[status]
            o.save()
            if created: new_inventory_count += 1
        print 'Found %d new inventory items' % new_inventory_count


    def do_collect_ghost_inventory(self):
        cursor = self._get_cursor()
        cursor.execute('''
        select i.upc, i.ref_category, e.code, i.name, c.name
            from entries e 
                inner join items i on i.id = e.ref_item
        left outer join categories c on i.ref_category = c.id
        ''')
        
        ghost_inventory = set()
        ghost_inventory_barcodes = set()
        for upc, category_id, barcode, title, platform in cursor.fetchall():
            if not upc:
                ghost_inventory_barcodes.add(barcode)
                print '------------\t%s\t%s\t%s' % (barcode, title, platform)
                continue
                
            item = self.get_item(upc, category_id)
            if not item:
                if upc in ghost_inventory:
                    continue
                ghost_inventory.add(upc)
                ghost_inventory_barcodes.add(barcode)
                print '%s\t%s\t%s\t%s' % (upc, barcode, title, platform)
        print 'Found %d ghost inventories.' % len(ghost_inventory_barcodes)

    def do_link_inventory_to_shipped_rent_orders(self):
        from project.inventory.models import Inventory

        def get_code_by_planed_id(planet_id):
            c = self._get_cursor()
            c.execute('''
                select r.sent_code  
                from endicia_labels e 
                    inner join history_records r on r.id = e.ref_history_record
                where
                    e.tracking_code = %s
            ''', [planet_id])
            for r in c.fetchall():
                return r[0]
            return None
        
        def get_code_by_upc(upc, sent_date, user):
            if isinstance(sent_date, datetime):
                sent_date = sent_date.date()
            c = self._get_cursor()
            c.execute('''
                select r.sent_code
                from history_records r
                    inner join items i on i.id = r.ref_item
                where
                    i.upc = %s
                    and cast(r.sent_date as date) = %s
                    and r.ref_user = %s
            ''', [upc, sent_date, user.id])
            for r in c.fetchall():
                return r[0]
            return None
        
        
        qs = RentOrder.objects.filter(inventory=None).order_by('-date_rent')
        i, total_count = 0, qs.count()
        for order in qs:
            barcode = None
            if order.incoming_tracking_number:
                barcode = get_code_by_planed_id(order.incoming_tracking_number)
            if not barcode and order.outgoing_tracking_number:
                barcode = get_code_by_planed_id(order.outgoing_tracking_number)
            if not barcode and order.date_rent:
                barcode = get_code_by_upc(order.item.upc, order.date_rent, order.user)
                
            inventory = None
            if barcode:
                try:
                    inventory = Inventory.objects.get(barcode__iexact=barcode)
                except Inventory.DoesNotExist:
                    print 'Inventory with barcode "%s" does not exist' % barcode

            if inventory:
#                print order.date_rent, order, inventory
                order.inventory = inventory
                order.save()
            
            i += 1
            if i % 100 == 0:
                print 'Processed %d of %d' % (i, total_count)

    def do_fix_inventory_manually(self):
        from project.inventory.models import Inventory

        for l in sys.stdin.readlines():
            l = l.strip()
            if not l:  continue
            from_id, to_id = l.split()
            print '%s --> %s' % (from_id, to_id)
            item = Item.objects.get(id=to_id)
            print 'Found item: %s, %s, %s' % (item, item.category, item.upc)
            c = self._get_cursor()
            c.execute('''
            select s.id `status`, c.name `condition`, e.code, e.ref_center
                from entries e
                    left outer join entry_conditions c on c.id = e.ref_entry_condition
                    left outer join entry_statuses s on s.id = e.ref_entry_status
            where e.ref_item = %s 
            ''', [from_id])
            for status, condition, barcode, ref_center in c.fetchall():
                print status, condition, barcode, ref_center
                if Inventory.objects.filter(barcode=barcode).count():
                    continue
                o = Inventory(
                    dropship_id=DROPSHIP_MAP[ref_center],
                    item=item,
                    barcode=barcode,
                    is_new=condition == 'New',
                    status = INVENTORY_STATUS_MAP[status],
                ) 
                o.save()
                print o

    def do_fix_old_rent_orders(self):
        qs = RentOrder.objects.filter(status=RentOrderStatus.Shipped)
        i, count = 0, qs.count()
        for r in qs:
            i += 1
            if i % 100 == 0:
                print '%s of %s' % (i, count)
            if not r.inventory:
                continue
            if r.inventory.status in [InventoryStatus.Lost, InventoryStatus.Sale, InventoryStatus.Sold]:
                r.status = RentOrderStatus.AutoCanceled
                r.save()
            elif r.inventory.status in [InventoryStatus.Damaged]:
                r.status = RentOrderStatus.AutoCanceled
                r.save()
            else:
                c = self._get_cursor()
                c.execute('''
                select not_expected_to_return
                    from entries e
                where e.code = %s 
                ''', [r.inventory.barcode])
                for not_expected_to_return, in c.fetchall():
                    if int(not_expected_to_return):
                        r.inventory.not_expected_to_return = True
                        r.inventory.save()
                        r.status = RentOrderStatus.AutoCanceled
                        r.save()
                    break
                
                if r.status == RentOrderStatus.Shipped:
                    plan = MemberRentalPlan.get_current_plan(r.user)
                    if not plan or plan.status == RentalPlanStatus.Canceled:
                        r.status = RentOrderStatus.AutoCanceled
                        r.save()
                        r.inventory.status = InventoryStatus.Unknown
                        r.inventory.save()
                        
    def do_fix_taxes(self):
        for b in BillingHistory.objects.all():
            if not b.debit:
                continue
            if b.tax == b.debit:
                b.tax = decimal.Decimal('0.0')
                b.save()

    def do_fix_rent_orders_8(self):
        d0 = datetime(2010, 11, 1)
        cursor = self._get_cursor()
        cursor.execute('''
            select 
                a.ref_user
            from 
                orders a
            where 
                (select b.ref_order_status from orders b where b.ref_user = a.ref_user order by id desc limit 1) = 8
        ''', [])
        for ref_user, in cursor.fetchall():
            try:
                rent_plan = MemberRentalPlan.objects.get(user__id=ref_user)
            except MemberRentalPlan.DoesNotExist:
                continue
            print rent_plan.user.id, rent_plan.user.email, rent_plan.next_payment_date, rent_plan
            for transaction in BillingHistory.objects.filter(user__id=ref_user, timestamp__gte=d0):
                print '    ', transaction.timestamp 


    def do_fix_billing_addresses(self):
        mcursor = self._get_cursor()
        mcursor.execute("""
            select u.id, m.billing_first_name, m.billing_last_name, 
            m.billing_address, m.billing_address2, m.billing_city, bs.code, m.billing_postal_code      
            from users u 
                left join members m on u.id=m.ref_user 
                left join states bs on bs.id=m.billing_ref_state 
            where u.id>3
                order by u.id
        """)
        i = 0
        for user_id, first_name, last_name, address1, address2, city, state, zip_code in mcursor.fetchall():
            try:
                cc = BillingCard.objects.get(user__id=user_id)
            except:
                continue

            if (cc.first_name or '').strip() == '' and (cc.last_name or '').strip() == '':             
                res = {
                    'first_name': first_name, 
                    'last_name': last_name,            
                }
                try:
                    res = settings.MELISSA.inaccurate_name(**res)
                except MelissaNameError:
                    pass
            
            if (cc.address1 or '').strip() == '':
                res = {
                    'address1': address1, 
                    'address2': address2, 
                    'city': city, 
                    'state': state, 
                    'zip_code': zip_code,
                }
                try:
                    res = settings.MELISSA.inaccurate_address(**res)
                except MelissaAddressError:
                    pass
                cc.address1 = res['address1']
                cc.address2 = res['address2']
                cc.city = res['city']
                cc.state = res['state']
                cc.county = res.get('county')
                cc.zip = res['zip_code']
                cc.save()
            i += 1
            if i % 100 == 0:
                print i

    def do_reformat_addresses(self):
        i = 0
        for p in Profile.objects.all():
            res = p.get_shipping_address_data()
            if 'address1' in res and res['address1']:
                res = settings.MELISSA.inaccurate_address(quiet=True, **res)
                p.set_shipping_address_data(res)
            i += 1
            if i % 100 == 0:
                print i
                
    def do_old_rent_plans(self):
        i, j = 0, 0
        for o in RentOrder.objects.filter(status=RentOrderStatus.Shipped).exclude(inventory=None).order_by('date_rent'):
#            if RentOrder.objects.filter(inventory=o.inventory, date_rent__gt=o.date_rent).count():
#                i += 1
#                o.status = RentOrderStatus.AutoCanceled
#                o.save()
#            elif RentOrder.objects.filter(status=RentOrderStatus.Returned, user=o.user, date_rent__gt=o.date_rent).count() > 5:
#                i += 1
#                o.status = RentOrderStatus.AutoCanceledByAstral
#                o.save()
#            else:
            plan = MemberRentalPlan.get_current_plan(o.user)
            if plan:
                print plan.status
#            if plan and plan.status == RentalPlanStatus.Canceled:
#                print o.user.id, '\t', o.date_rent, '\t', o, plan
#                i += 1 
#            else:
#                claims = Claim.objects.filter(object_id=o.id).filter(Q(type=ClaimType.GameIsDamaged) | Q(type=ClaimType.DontRecieve))
#                if claims.count():
#                    print o.user.id, '\t', o
#                    for c in claims:
#                        print '    ', c.get_title() 
#            else:
#                print o.id, '\t', o.user.id, '\t', o.date_rent
#            elif o.incoming_tracking_number:
#                res = endicia.status_request(o.incoming_tracking_number)
#                print res
            j += 1
        print i, 'of', j


    def do_fix_next_payments(self):
        today = datetime.now().date()
        for p in MemberRentalPlan.objects.filter(status=RentalPlanStatus.Active):
            nd = p.next_payment_date
            b = None
            for b in BillingHistory.objects.filter(user=p.user, type=TransactionType.RentPayment, status=TransactionStatus.Passed):
                break
            if not b:
                continue
            if b.timestamp >= datetime(2010, 11, 04):
                continue
            nnp = RentalPlan.get_next_payment(p.plan, p.start_date, b.timestamp.date())
            if not nnp:
                continue
            date, _amount = nnp
            if nd == date:
                continue
            if date <= today:
                continue
            p.next_payment_date = date
            p.save()

    def do_fix_delinquent_status(self):
        dX = datetime(2010, 11, 01)
        for p in MemberRentalPlan.objects.filter(status=RentalPlanStatus.Delinquent):
            if BillingHistory.objects.filter(user=p.user, type=TransactionType.RentPayment, status=TransactionStatus.Passed, 
                                             timestamp__gte=dX).count():
                print p.user.id 

    def do_fix_accounts(self):
        for u in User.objects.filter(is_active=False):
            if u.get_profile().activation_code:
                print u.id, '---'
            else:
                print u.id, 'oooooo'
                u.is_active = True
                u.save()

    def do_fix_payments(self):
        for p in BillingHistory.objects.filter(aim_transaction_id=None).exclude(aim_response=None):
            transaction_id = p.aim_response.get('transaction_id')
            if int(transaction_id):
                p.aim_transaction_id = transaction_id
                p.save()
                print p.id, p.aim_response['transaction_id']
