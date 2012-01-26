import MySQLdb
import base64
import decimal
import os #@UnusedImport
from logging import debug #@UnusedImport
from datetime import datetime
import re

from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User 
from django.contrib.sites.models import Site
from django.db import transaction #@UnusedImport

from project.rent.models import RentalPlanStatus, MemberRentalPlan, RentOrder,\
    RentOrderStatus
from project.buy_orders.models import BuyOrder, BuyOrderItem, BuyOrderItemStatus,\
    BuyOrderStatus, PackSlip, PackSlipItem
from project.catalog.models import Item, Category, ItemVote, Review
from project.rent.models import RentList
from project.claims.models import GamemineNotReceiveGameClaim
from project.subscription.models import Subscriber
from project.members.models import Profile , BillingHistory, TransactionStatus,\
    TransactionType, Refund
from project.inventory.models import Inventory, InventoryStatus, Dropship
import itertools #@UnusedImport
from django.conf import settings


def canonize_upc(upc):
    return upc
#    upc = str(upc)
#    l = len(upc)
#    if l > 32:
#        print 'Warning: len(upc) > 32: %s' % upc
#        return upc
#    return ('0' * (32 - l)) + upc

def update_dict(dst, src, prefix=''):
    for k, v in src.items():
        dst['_'.join(filter(None, (prefix, k)))] = v
    return dst

class Command(NoArgsCommand):
    help = 'Import old data'
    
    CARD_TYPE_MAP = {
        'American Express': 'american-express',                     
        'Discover': 'discover',                     
        'Visa': 'visa',                     
        'MasterCard': 'master-card',                     
    }
    
    PLAN_MAP = {
        1: 0,   # 1 Game Plan -> 1 Game - Monthly - Unlimited
        2: 12,  # 1 Game Plan - 6 Months -> 1 Game Plan - 6 months
        3: 13,  # 1 Game Plan - 12 Months -> 1 Game Plan - 12 Months
        4: 1,  # 2 Games Plan -> Monthly 2 Game Plan
        7: 2,  # 2 Games Plan - 6 Months -> 6 Months 2 Game Plan
        8: 18, # 2 Games Plan - 12 Months -> 2 Games Plan - 12 Months 
        9: 19,  # 3 Games Plan -> Monthly 2 Game Plan
        10: 20,  # 3 Games Plan - 6 Months -> 6 Months 2 Game Plan
        11: 21, # 3 Games Plan - 12 Months -> 2 Games Plan - 12 Months 
    }

    DROPSHIP_MAP = {
        1: 2, # NJ
        2: 1, # FL
        3: 3, # NV
    }

    
    PLAN_STATUS_MAP = {
        1: RentalPlanStatus.Active, # Active
        3: RentalPlanStatus.AutoCanceled, # Check Pending
        4: 7, #RentalPlanStatus.Canceled, # Canceled
        5: RentalPlanStatus.Active, # Pending
        6: RentalPlanStatus.Delinquent, #  Suspended 
        7: 8, # RentalPlanStatus.CanceledP # Cancel Pending
        8: RentalPlanStatus.Canceled, # Canceled for upgrade 
        9: RentalPlanStatus.Active, # Free Trial
        10: RentalPlanStatus.Collection, #Sent To Collection
        11: RentalPlanStatus.AutoCanceled, #Auto Canceled
        12: RentalPlanStatus.Delinquent,                        
    }
    
    BUY_STATUS_MAP = {
        1: 6, # Paid -> Shipped
        2: 4, # Declined -> Canceled
        3: 2, # Pending -> Pending
        4: 2, # Authorized -> Pending
        6: 4, # Cancel -> Canceled
        8: 1, # Processed -> Checkout
        9: 9, # Back-ordered -> Chargeback
        10: 3, # Pre-ordered -> Pre Order
        11: 6, # Shipped -> Shipped
        12: 4, # Problem -> Cancel
    }
    
    SURVEY_SYSTEM_MAP = {
        67: 3, # PlayStation-3-Games 
        68: 1, # Xbox-360-Games 
        69: 6, # Nintendo-Wii-Games 
        70: 5, # Sony-PSP-Games 
        71: 7, # Nintendo-DS-Games 
        72: 4, # PlayStation-2-Games 
        73: 2, # Xbox-Games 
        74: 8, # GameCube-Games 
        75: 12, # psp-movies 
    }
    

    """
    OLD:
    1    Member never received the game
    2    Gamemine never received member's game return
    3    Member received the wrong game
    4    The game arrived in the wrong sleeve
    5    Member sent back the wrong game
    6    Member sent back the wrong sleeve
    7    The game was scratched, damaged or unplayable
    8    Memberlost or damaged the game
    9    Member lost the game's sleeve
    10    Member lost the game's shipping envelope and need a new mailer
    11    Member lost the game
    12    Member damaged the gamemine
    NEW:
    (0, 'Game is damaged, scratched or unplayable'),
    (1, 'I received the wrong Game'),
    (2, 'I haven\'t received the Game'),
    (3, 'The mailer was empty'),
    (4, 'I mailed the game back but Gamemine has not received it'),
    (5, 'I mailed the game but Gamemine has not received it'),
    (6, 'I received the wrong trade value credit for my game'),
    """
    CLAIM_TYPES_MAP = {
        1: 2,
        2: 5,
        3: 1,
        4: 1,
        5: 1,
        6: 1,
        7: 0,
        8: 0,
        9: 0,
        10: 0,
        11: 0,
        12: 0,
    }
    
    def decrypt(self, s):
        key = 'QSCreditCardSecure'
        result = ''
        string = base64.b64decode(s)
        for i in xrange(len(string)):
            char = string[i]
            keychar = key[i % len(key)-1] 
            char = chr(ord(char)-ord(keychar)) 
            result += char
        return result
    
    def get_states(self):
        self.STATES = {}
        c = self.mconn.cursor()
        c.execute("select id, code from states") 
        rows = c.fetchall()
        for id, code in rows:
            self.STATES[id] = code

    def get_items(self):
        self.items = {}
        for i in Item.objects.all():
            self.items[canonize_upc(i.upc)] = i

    def get_item(self, upc):
#        print 'UPC %s not found' % upc
        if not upc:
            return None
#        if upc in self.items:
#            os.write(1, '.')
        item = self.items.get(canonize_upc(upc))
        if item:
            return item
        for k, v in self.items.items():
            if re.search(upc, k):
#                print 'Found %s in %s' % (upc, k)
                return v
        return None 

    def get_categories(self):
        self.categories = {}
        for i in Category.objects.all():
            self.categories[i.id] = i
            
    def fix_address(self, res):
        if not settings.MELISSA:
            return res
        try:
            #print 'Got: %s, %s %s, %s' % (' '.join(filter(None, [res['address1', 'address2']])), res['city'], res['state'], res['zip'])
            res = settings.MELISSA.inaccurate_address(**res)
            #print ' ->: %s, %s %s, %s' % (' '.join(filter(None, [res['address1', 'address2']])), res['city'], res['state'], res['zip'])
            return res
        except Exception, e:
            if res['address1']:
                print '------------------------------------------------------------------------------'
                print e
                print '------------------------------------------------------------------------------'
            return res
        
    def fix_name(self, name):
        if not settings.MELISSA:
            return name
        try:
            #print 'Got: %s' % name
            if not isinstance(name, dict):
                name = {'full_name': name}
            res = settings.MELISSA.inaccurate_name(**name)
            #print ' ->: %s %s' % (res['first_name'], res['last_name'])
            return res
        except Exception, e:
            if name:
                print e
            return name
           
    def import_billing_card(self, p):
        c = self.mconn.cursor()
        c.execute("""
            select 
                bc.cc_type, bc.cc_num, bc.cc_code, bc.cc_expire_month, bc.cc_expire_year, bc.cc_name, bc.billing_address, bc.billing_city, s.code, bc.billing_zip_code
            from shop_credit_cards bc 
            inner join states s on bc.billing_ref_state=s.id 
            where bc.ref_user=%s 
            order by bc.id desc 
        """, p.user_id)
        rows = c.fetchall()
        if len(rows)>0:
            cc_type, cc_num, cc_code, cc_expire_month, cc_expire_year, cardholder_name, billing_address, billing_city, billing_state, billing_zip_code = rows[0]
            if cc_type in self.CARD_TYPE_MAP:
                card_data = {
                    'type': cc_type,
                    'number': self.decrypt(cc_num),
                    'exp_year': cc_expire_year,
                    'exp_month': cc_expire_month,
                    'code': cc_code,
                }
                p.set_billing_card_data(card_data)
                p.set_billing_name_data(self.fix_name(cardholder_name))
                
                address_data = {
                    'address1': billing_address,
                    'address2': '',
                    'city': billing_city,
                    'state': billing_state,
                    #'country': 'USA',
                    'zip_code': billing_zip_code,
                }
                p.set_billing_address_data(self.fix_address(address_data))
                
        c.execute("select cc_type, cc_num, cc_code, cc_expire_month, cc_expire_year, cc_name from credit_cards where ref_user=%s order by is_valid desc, id desc", p.user_id)
        rows = c.fetchall()
        if len(rows)>0:
            cc_type, cc_num, cc_code, cc_expire_month, cc_expire_year, cardholder_name = rows[0] 
            card_data = {
                'type': cc_type,
                'number': self.decrypt(cc_num),
                'exp_year': cc_expire_year,
                'exp_month': cc_expire_month,
                'code': cc_code,
            }
            p.set_billing_card_data(card_data)
            p.set_billing_name_data(self.fix_name(cardholder_name))


    def import_rent_plan(self, user_id):
        ocursor = self.mconn.cursor()
        ocursor.execute("select id, ref_package, ref_order_status, signup_amount, billing_amount, included_tax_amount, billing_period, order_date, start_date, expire_date, next_billing_date, paypal_id, paypal_cc, paypal_cc_expire, paypal_nextbilling_date, paypal_status, paypal_amount, paypal_num_of_failed_payments, sent_count, wish_count, returned_count, prepared_count, items_to_send, items_to_send_basic, is_hotlist_order, next_payment_number, note, authorize_transaction_id, times_billed, ref_credit_card, takes_part_in_picklist, checked_paypal_transactions, non_recurring, promotional, paid_by_check, suspend_date, cancel_date, capture_authorization_failed, capture_authorization_attempts, capture_authorization_fail_date from orders where ref_user=%s order by id desc", [user_id,])
        ro = ocursor.fetchall()

        if len(ro) > 0:
            field_names = map(lambda x: x[0], ocursor.description)
            r = dict(zip(field_names, ro[0]))
            if r['ref_package'] in self.PLAN_MAP and r['ref_order_status'] in self.PLAN_STATUS_MAP:
                mrp = MemberRentalPlan(
                    user_id = user_id,
                    plan = self.PLAN_MAP[r['ref_package']],
#                    status = RentalPlanStatus.AutoCanceled, #self.PLAN_STATUS_MAP[r['ref_order_status']],
                    status = self.PLAN_STATUS_MAP[r['ref_order_status']],
                    created = r['order_date'],
                    start_date = r['start_date'],
                    expiration_date = r['cancel_date'],
                    next_payment_date = r['next_billing_date'],
                    next_payment_amount = decimal.Decimal('%.02f' % r['paypal_amount']),
                )
                mrp.save()
            
                
    def import_buy_orders(self, user_id):
        ocursor = self.mconn.cursor()
        icursor = self.mconn.cursor()
        ocursor.execute("select * from shop_orders where ref_user=%s order by id", [user_id,])
        order_field_names = map(lambda x: x[0], ocursor.description)
        for ro in ocursor.fetchall():
            o = dict(zip(order_field_names, ro))
            
            data = {}
            update_dict(data, self.fix_name({
                'first_name': o['first_name'],
                'last_name': o['last_name'],
            }))
            update_dict(data, self.fix_address({
                'address1': o['address'], 
                'address2': o['address2'], 
                'city': o['city'], 
                'state': self.STATES[o['ref_state']], 
                #'country': 'USA', 
                'zip_code': o['postal_code'], 
            }), 'shipping')
            update_dict(data, self.fix_name({
                'first_name': o['billing_first_name'],
                'last_name': o['billing_last_name'],
            }), 'billing')
            update_dict(data, self.fix_address({
                'address1': o['billing_address'], 
                'address2': o['billing_address2'], 
                'city': o['billing_city'], 
                'state': self.STATES[o['billing_ref_state']], 
                #'country': 'USA', 
                'zip_code': o['billing_postal_code'], 
            }), 'billing')
            
            status = self.BUY_STATUS_MAP[o['ref_order_status']]
            if status == 6: #shipped
                if o['ref_shipping_status'] == 4: # cancelled
                    status = 4 # Canceled 
            
            bo = BuyOrder(
                id = o['id'], 
                user_id = user_id,
                status = status,
                create_date = o['order_date'],

                tax = decimal.Decimal('%.02f' % o['tax_fee']),
                total = decimal.Decimal('%.02f' % o['total']),
                
                **data
            )
            bo.save()
            
            icursor = self.mconn.cursor()
            icursor.execute("select i.price, i.count, r.upc, r.id from shop_order_items i left join items r on i.ref_item=r.id where i.ref_order=%s order by i.id", o['id'])
            for i_price, i_count, i_upc, r_id in icursor.fetchall():
                item = self.get_item(i_upc)
                if not item: 
                    self.missing_items.add(r_id)
                    continue
                status = BuyOrderItemStatus.Shipped if bo.status == BuyOrderStatus.Shipped else BuyOrderItemStatus.Canceled  
                for _qty in xrange(i_count): 
                    boi = BuyOrderItem(
                        order = bo,
                        status = status,
                        item = item,
                        price = decimal.Decimal(str(i_price))
                        )
                    boi.save()
                    
            if bo.status == BuyOrderStatus.Shipped:
                
                icursor = self.mconn.cursor()
                image_filename, tracking_code = None, None
                icursor.execute("SELECT image_filename, tracking_code FROM endicia_labels e where ref_shop_order = %s", o['id'])
                for image_filename, tracking_code in icursor.fetchall():
                    break
                                
                if image_filename:
                    image_filename = 'media/labels/old/endicia/' + image_filename 
                                
                pack_slip = PackSlip(
                    order = bo,
                    created = bo.create_date,
                    mail_label = image_filename,
                    tracking_number = tracking_code,
                    date_shipped = bo.create_date,
                )
                pack_slip.save()
                for order_item in bo.items.all():
                    PackSlipItem(
                        slip = pack_slip,
                        order_item = order_item,
                        added = bo.create_date,
                    ).save()


    def import_rent_list(self, user_id):
        c = self.mconn.cursor()
        c.execute("select w.add_date, w.position, i.upc, i.id from wishes w inner join items i on w.ref_item=i.id where w.ref_user=%s order by w.id", [user_id,])
        for add_date, position, upc, id in c.fetchall():
            item = self.get_item(upc)
            if not item: 
                self.missing_items.add(id)
                continue 
            rl = RentList(
                user_id = user_id,
                item = item,
                order = position,
                added = add_date
                )
            rl.save()

    def import_shipping_problem_reports(self, user_id):
        c = self.mconn.cursor()
        c.execute("select s.add_date, s.ref_shipping_problem, i.upc, i.id from shipping_problem_reports s inner join items i on s.ref_item=i.id where s.ref_user=%s order by s.id", [user_id,])
        for add_date, ref_shipping_problem, upc, id in c.fetchall():
            if add_date is not None and ref_shipping_problem in self.CLAIM_TYPES_MAP:
                item = self.get_item(upc)
                if not item: 
                    self.missing_items.add(id)
                    continue 
                o = GamemineNotReceiveGameClaim(
                    user_id = user_id,
                    claim_object = item,
                    date = add_date,
                    mailed_date = add_date,
                    sphere_of_claim = 2,
                    type = self.CLAIM_TYPES_MAP[ref_shipping_problem]
                )
                o.save()
                
    def import_system_own(self, p):
        c = self.mconn.cursor()
        c.execute("select ref_survey_option from survey_stats where ref_survey_question=16 and ref_user=%s", [p.user_id,])
        for [ref_survey_option] in c.fetchall():
            p.owned_systems.add(self.categories[self.SURVEY_SYSTEM_MAP[ref_survey_option]])
            
    def import_subscripton(self):
        c = self.mconn.cursor()
        c.execute("select email, name, subscription_date from subscribers")
        for email, _name, subscription_date in c.fetchall():
            s = Subscriber(email=email, active=True, timestamp=subscription_date)
            s.save()

    def import_votes(self, user_id):
        c = self.mconn.cursor()
        c.execute("select s.vote_date, s.ratio, s.host_ip, i.upc, i.id from item_votes s inner join items i on s.ref_item=i.id where s.ref_user=%s order by s.id", [user_id,])
        for vote_date, ratio, host_ip, upc, id in c.fetchall():
            if vote_date is not None:
                item = self.get_item(upc)
                if not item: 
                    self.missing_items.add(id)
                    continue 
                o = ItemVote(
                    user_id = user_id,
                    item = item,
                    timestamp = vote_date,
                    ratio = ratio,
                    ip_address = host_ip
                )
                o.save()

    def import_reviews(self, user_id):
        c = self.mconn.cursor()
        site = Site.objects.get_current()
        c.execute("select s.date_posted, s.title, s.body, i.upc, i.id from item_reviews s inner join items i on s.ref_item=i.id where s.ref_user=%s order by s.id", [user_id,])
        for date_posted, title, body, upc, id in c.fetchall():
            if date_posted is not None:
                item = self.get_item(upc)
                if not item: 
                    self.missing_items.add(id)
                    continue 
                o = Review(
                    user_id = user_id,
                    site = site,
                    content_object = item,
                    title = title.decode('utf-8', 'ignore'),
                    comment = body.decode('utf-8', 'ignore'),
                    rating = 5
                )
                date_posted
                o.timestamp = date_posted
                o.save()
                ItemVote(
                    user_id=user_id,
                    item=item,
                    timestamp=date_posted,
                    ratio=5,
                    review=o
                ).save()
                
    def import_rent_orders(self, user_id):
        user = User.objects.get(id=user_id)
        shipping = user.get_profile().get_shipping_address_data('shipping')
        
        def get_label_data(history_record_id, label_type):
            c = self.mconn.cursor()
            c.execute('''
                select image_filename, tracking_code FROM endicia_labels where ref_history_record = %s and label_type = %s
            ''', [history_record_id, label_type])
            for image_filename, tracking_code in c.fetchall():
                return image_filename, tracking_code
            return None, None
        
        c = self.mconn.cursor()
        c.execute('''
            select 
                i.upc, 
                h.sent_date, 
                group_concat(h.delivered_date order by h.delivered_date), 
                h.sent_code, 
                group_concat(h.from_center order by h.from_center), 
                group_concat(h.returned_date order by h.returned_date), 
                group_concat(h.id order by h.id)
            from history_records h
                inner join items i on i.id=h.ref_item
            where h.ref_user = %s
            group by h.ref_item, h.sent_date, h.sent_code
            order by h.sent_date
        ''', [user_id,])
        for upc, sent_date, delivered_date, sent_code, from_center, returned_date, history_record_id in c.fetchall():
            delivered_date = delivered_date.split(',')[-1]
            delivered_date = datetime.strptime(delivered_date, '%Y-%m-%d %H:%M:%S') if delivered_date != '0000-00-00 00:00:00' else None
            from_center = int(from_center.split(',')[-1])
            returned_date = returned_date.split(',')[-1]
            returned_date = datetime.strptime(returned_date, '%Y-%m-%d') if returned_date != '0000-00-00' else None
            history_record_id = int(history_record_id.split(',')[-1])

            item = self.get_item(upc)
            if not item: 
                if returned_date is None:
                    self.missing_items.add(id)
                continue 
            
            outgoing_mail_label, outgoing_tracking_number = get_label_data(history_record_id, 'rental_mailing')
            incoming_mail_label, incoming_tracking_number = get_label_data(history_record_id, 'rental_return')
            
            if outgoing_mail_label:
                outgoing_mail_label = 'media/labels/old/endicia/' + outgoing_mail_label
            if incoming_mail_label:
                incoming_mail_label = 'media/labels/old/endicia/' + incoming_mail_label
            
            o = RentOrder(
                user = user,
                item = item,
                status = RentOrderStatus.Returned if returned_date else RentOrderStatus.Shipped,
                date_rent = sent_date,
                date_prepared = sent_date,
                date_shipped = sent_date,
                date_delivered = delivered_date,
                date_returned = returned_date,
                
                source_dc_id = self.DROPSHIP_MAP.get(from_center),
                inventory = self.entries.get(sent_code),
    
                first_name = user.first_name,
                last_name = user.last_name,

                outgoing_mail_label = outgoing_mail_label,
                outgoing_tracking_number = outgoing_tracking_number,
                incoming_mail_label = incoming_mail_label,
                incoming_tracking_number = incoming_tracking_number,
                
                **shipping
            )
            o.save()

    def import_inventory(self):
        statuses = {
            1: InventoryStatus.InStock, # Available
            2: InventoryStatus.Rented, # Rented
            3: InventoryStatus.Sold, # Sold
            4: InventoryStatus.Damaged, # Damaged
            5: InventoryStatus.Pending, # Invoiced
            6: InventoryStatus.Lost, # Lost
            7: InventoryStatus.Sale, # Left to canceled member
        }
        
        self.entries = {}

        c = self.mconn.cursor()
        c.execute('''
        select i.upc, i.id item_id, s.id `status`, c.name `condition`, e.code, e.ref_center, e.id
            from entries e 
                inner join items i on i.id = e.ref_item
                left outer join entry_statuses s on s.id = e.ref_entry_status
                left outer join join entry_conditions c on c.id = e.ref_entry_condition
        ''')
        for upc, id, status, condition, barcode, ref_center, _entry_id in c.fetchall():
            item = self.get_item(upc)
            if not item: 
                self.missing_items.add(id)
                continue 
            o = Inventory(
                dropship_id=self.DROPSHIP_MAP[ref_center],
                item=item,
                barcode=barcode,
                is_new=condition == 'New',
                status = statuses[status],
            ) 
            o.save()
            self.entries[barcode] = o
        print 'Found: %s' % Inventory.objects.all().count()
        
    def import_billing_history(self, user_id):
        c = self.mconn.cursor()
        c.execute('''
            select p.date, p.amount, p.included_tax_amount, p.comment, p1.amount refund, p1.date refund_date, p1.comment refund_comment, h.cc_num, p.id
            from payments p 
                left outer join payments p1 on (p1.ref_transaction_id = p.transaction_id and p1.trxtype = 'C')
                left outer join billing_history_records h on (h.trans_id = p.transaction_id)
            where p.trxtype in ('D', 'S') and p.ref_user = %s
            group by p.id
        ''', [user_id])
        for date, amount, tax, comment, refund, refund_date, refund_comment, cc_num, _id in c.fetchall():
            cc_num = 'XXXX-XXXX-XXXX-' + cc_num[-4:] if cc_num else ''
            o = BillingHistory(
                user_id = user_id,
                timestamp = date,
                payment_method = cc_num,
                description = comment,
                debit = decimal.Decimal('%.02f' % amount),
                tax = decimal.Decimal('%.02f' % tax) if tax else decimal.Decimal('0.0'),
                status = TransactionStatus.Passed, 
                type = TransactionType.RentPayment,
            )
            o.save()
            if refund:
                r = Refund(
                    payment = o,
                    amount = decimal.Decimal('%.02f' % refund),
                    comment = refund_comment,
                    timestamp = refund_date,
                )
                r.save()


#    @transaction.commit_on_success                
    def handle_noargs(self, **options):
        
        self.mconn = MySQLdb.connect(host='78.31.177.17', db="gamemine", user='gamemine', passwd='1')
#        self.mconn = MySQLdb.connect(host='localhost', db="gamemine", user='root', passwd='')
        
        self.missing_items = set()
        
        print "Get States"
        self.get_states()
        print "Get Items"
        self.get_items()
        print "Get Categories"
        self.get_categories()

        print "Get Subscription"
        self.import_subscripton()

        print "Get Inventory"
        self.import_inventory()

        print "Get Users"
        mcursor = self.mconn.cursor()
        mcursor.execute("""
            select 
                u.id, u.name, u.password, u.email, u.ref_account_type, u.ref_account_status, u.lastlogin_date, u.reg_date, u.user_name, u.ref_center, 
                m.first_name, m.last_name, m.address, m.address2, m.city, m.postal_code, m.phone, ss.code, 
                m.billing_first_name, m.billing_last_name, m.billing_postal_code, m.billing_address, m.billing_address2, m.billing_city, bs.code      
            from users u 
            left join members m on u.id=m.ref_user 
            left join states ss on ss.id=m.ref_state 
            left join states bs on bs.id=m.billing_ref_state 
            where u.id>3
            order by u.id
        """)
        rows = mcursor.fetchall()
        unames = []
        uemails = []
        cnt = 0
        for (id, name, password, email, ref_account_type, ref_account_status, lastlogin_date, reg_date, user_name, ref_center, first_name, last_name, address, address2, city, postal_code, phone, state, billing_first_name, billing_last_name, billing_postal_code, billing_address, billing_address2, billing_city, billing_state) in rows: #@UnusedVariable
            
            if name is None:
                name = email[:30]
            else:
                name = name[:30]
            if name in unames:
                continue
            unames.append(name)

            
            cnt += 1
            if cnt % 100==0:
#                if cnt > 500:
#                    break
                print cnt

#            if cnt < 9000:
#                continue

            
            email = email[:75]
            if email in uemails:
                continue
            uemails.append(email)
            
            if first_name is not None:
                first_name = first_name[:30]
            else:
                first_name = ''

            if last_name is not None:
                last_name = last_name[:30]
            else:
                last_name = ''

            u, _c = User.objects.get_or_create(id=id, username=name, email=email)
            u.date_joined = reg_date
            user_full_name = settings.MELISSA.inaccurate_name(full_name='%s %s' % (first_name, last_name))
            u.first_name = user_full_name['first_name']
            u.last_name = user_full_name['last_name']
            
            if lastlogin_date is not None:
                u.last_login=lastlogin_date
            
            if ref_account_status==1:
                u.is_active = True
                account_status = 0
            else:
                u.is_active = False
                account_status = 2
            u.set_password(password)
            u.save()
            
            if postal_code is not None:
                if len(postal_code)>10:
                    postal_code = None
                    
            dropship_id = self.DROPSHIP_MAP.get(ref_center)
            dropship = Dropship.objects.get(id=dropship_id) if dropship_id else None

            data = {}
            update_dict(data, {
                'address1': address,
                'address2': address2,
                'city': city,
                'state': state,
                'zip': postal_code,
            }, 'shipping')
            
            p, _c = Profile.objects.get_or_create(
                user = u,
                account_status = account_status,
                dropship = dropship,
                **data 
            )
            p.save()

            self.import_billing_card(p)
            self.import_rent_plan(id)
            self.import_buy_orders(id)
            self.import_rent_list(id)
            self.import_rent_orders(id)
            self.import_shipping_problem_reports(id)
            self.import_system_own(p)
            self.import_votes(id)
            self.import_reviews(id)
            self.import_billing_history(id)


        print "Fixing buy orders..."
        def chain_objects(o1, objects=[]):
            return itertools.chain([o1] if o1 else [], itertools.ifilter(lambda x: x != o1, objects))
    
        def find_dropship(item, is_new, zip_code, profile):
            dropships = list(chain_objects(profile.dropship, Dropship.list_by_distance(zip_code)))
            for dropship in dropships:
                if dropship.is_game_available(item, is_new):
                    return dropship
            return None
    
        picked_list = BuyOrderItem.objects.filter(status=BuyOrderItemStatus.Pending)
        for p in picked_list:
            if p.source_dc:
                continue
            zip_code = p.order.shipping_zip_code
            profile = p.order.user.get_profile()            
            p.source_dc = find_dropship(p.item, p.is_new, zip_code, profile)
            p.save()
        
        print "Users", cnt
        print "Found %s missing items" % len(self.missing_items)
        print 'Saving missing item...'
        with open('data/missing-items.txt', 'w') as f:
            for id in self.missing_items:
                c = self.mconn.cursor()
                c.execute("select i.upc, i.name, c.name2 from items i left outer join categories c on c.id = i.ref_category where i.id = %s", [id,])
                for row in c.fetchall():
                    print >>f, '\t'.join(row)

        from project.management.commands.catalog import Command
        command = Command()
        command.handle_label('fix_counters')
                    
        print 'DONE'
