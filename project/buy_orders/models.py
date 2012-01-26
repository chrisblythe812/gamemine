import itertools
import decimal
import base64
import logging
from uuid import uuid4
from datetime import datetime, timedelta
import re

from endiciapy import Endicia, ImageFormat, MailClass, MailpieceShape

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import signals
from django.core.files.base import ContentFile
from django.db import transaction

from django_snippets.models import BlowfishField
from django_snippets.thirdparty.models import JSONField

from project.members.models import CREDIT_CARD_TYPES
from project.claims.models import Claim
from project.taxes.models import Tax
from project.utils.mailer import mail
from project.utils import create_aim

logger = logging.getLogger(__name__)

def split_zip(zip):
    z = zip.split('-')
    z += ['0000'] * (2 - len(z))
    return z


class BuyCartCompleteException(Exception):
    def __init__(self, message):
        self.message = message


class BuyCart(models.Model):
    user = models.OneToOneField(User, null=True)
    anonymous_cart_id = models.CharField(max_length=40, null=True, db_index=True)
    size = models.IntegerField(default=0)
    modified = models.DateTimeField(auto_now=True, default=datetime.now)
    last_session_timestamp = models.DateTimeField(null=True)
    applied_credits = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))

    @staticmethod
    @transaction.commit_on_success
    def get(request):
        if request.user.is_authenticated():
            if 'cart_id' in request.session:
                cart_id = request.session['cart_id']
                cart, created = BuyCart.objects.get_or_create(anonymous_cart_id=cart_id) #@UnusedVariable
                if cart.size:
                    BuyCart.objects.filter(user=request.user).delete()
                    cart.user = request.user
                    cart.anonymous_cart_id = None
                    cart.save()
                else:
                    cart.delete()
                    cart, created = BuyCart.objects.get_or_create(user=request.user) #@UnusedVariable
                del request.session['cart_id']
            else:
                cart, created = BuyCart.objects.get_or_create(user=request.user) #@UnusedVariable
        else:
            if 'cart_id' not in request.session:
                request.session['cart_id'] = str(uuid4())
            cart_id = request.session['cart_id']
            cart = BuyCart.objects.filter(anonymous_cart_id=cart_id)
            if cart.count():
                cart = cart[0]
            else:
                cart = BuyCart(anonymous_cart_id=cart_id)
                cart.save()
        cart.request = request
        return cart


    def push_item(self, request, item, quantity=1, inc_quantity=None, is_new=True):
        if is_new:
            if not (item.available_for_selling_n() and item.retail_price_new > 0):
                return
        else:
            if not (item.available_for_selling_u() and item.retail_price_used > 0):
                return

        try:
            cart_item = self.items.get(item=item, is_new=is_new)
        except BuyCartItem.DoesNotExist:
            cart_item = BuyCartItem(cart=self,
                                    item=item,
                                    user_session_id=request.current_session_id,
                                    is_new=is_new)
            cart_item.user_session_price = item.retail_price_new if is_new else item.retail_price_used

        if inc_quantity:
            cart_item.quantity += inc_quantity
        else:
            cart_item.quantity = quantity

        if cart_item.quantity:
            cart_item.save()
        else:
            cart_item.delete()

        self._recalc_size()
        self.save()

    def remove(self, cart_item):
        self.items.filter(id=cart_item.id).delete()
        self._recalc_size()
        self.save()

    def empty(self):
        self.items.all().delete()
        self.size = 0
        self.applied_credits = 0
        self.save()

    def calc_total(self):
        total = 0
        for i in self.items.all():
            total += i.quantity * i.get_price(self.request)
        return total - self.get_discount_amount()
    total = property(calc_total)

    def get_items(self, **kwargs):
        for i in self.items.filter(**kwargs):
            i.request = self.request
            yield i

    def recalc(self):
        self._recalc_size()
        self.save()

    def _recalc_size(self):
        self.size = self.items.aggregate(models.Sum('quantity'))['quantity__sum'] or 0

    @staticmethod
    def purge():
        time_x = datetime.now() - timedelta(minutes=settings.CART_SESSION_LIFETIME)
        q = BuyCart.objects.filter(last_session_timestamp__lt=time_x)
        logger.debug('Purging %d cart(s)...', q.count())
        q.delete()

    def get_discount_amount(self):
        if self.request.user.is_authenticated() and BuyOrder.objects.filter(user=self.request.user, discounts__gt=0).count() > 0:
            return decimal.Decimal('0.00')

        if self.items.filter(is_new=True).count() > 0 and self.items.filter(is_new=False).count() > 0:
            p = min(map(lambda x: x.price, self.get_items(is_new=False))) / 2
        else:
            p = 0
        return decimal.Decimal('%.2f' % p)


class BuyCartItem(models.Model):
    class Meta:
        ordering = ['id']

    cart = models.ForeignKey(BuyCart, related_name='items')
    item = models.ForeignKey('catalog.Item')
    quantity = models.IntegerField(default=0)
    is_new = models.BooleanField(default=True, db_index=True)
    user_session_id = models.CharField(max_length=40)
    user_session_price = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.0'))
    created = models.DateTimeField(default=datetime.now)

    def get_retail_price(self):
        if self.item.release_date > datetime.now().date() + timedelta(30):
            return 0
        if self.is_new:
            if self.item.available_for_selling_n() and self.item.retail_price_new > 0:
                return self.item.retail_price_new
        else:
            if self.item.available_for_selling_u() and self.item.retail_price_used > 0:
                return self.item.retail_price_used

    def get_price(self, request=None):
        request = request or self.request
        if request.current_session_id == self.user_session_id:
            return self.user_session_price
        else:
            return self.get_retail_price()
    price = property(get_price)

    def get_total(self, request=None):
        request = request or self.request
        return self.quantity * self.get_price(request)
    total = property(get_total)


class BuyOrderStatus:
    New = 0
    Checkout = 1
    Pending = 2
    PreOrder = 3
    Canceled = 4
    AutoCancel = 5
    Shipped = 6
    Delivered = 7
    Refund = 8
    Chargeback = 9
    Problem = 10

BUY_ORDER_STATUS = (
    (0, 'New'),
    (1, 'Checkout'),    # The order checkout by the Customer is pending completion.
    (2, 'Pending'),     # The order checkout by the Customer was completed for "In Stock" items.
    (3, 'Pre Order'),   # The order checkout by the Customer was completed for "Unreleased" items.
    (4, 'Canceled'),    # The order was canceled by the Customer before it was processed.
    (5, 'Auto Cancel'), # The order was auto canceled before it was processed due to billing issue.
    (6, 'Shipped'),     # The order was shipped by the Distribution Center to Customer.
    (7, 'Delivered'),   # The order was delivered by the US Postal Service to Customer.
    (8, 'Refund'),      # The order was refunded, partially refunded or voided by the Distribution Center.
    (9, 'Chargeback'),  # The order was disputed and refunded by the Customer's Bank.
    (10, 'Problem'),     # The Customer submitted a problem claim ticket for the order.
)

class BuyOrder(models.Model):
    class Meta:
        ordering = ['-create_date']

    user = models.ForeignKey(User, editable=False, null=True) # null=True is required for checkout --pashka
    status = models.IntegerField(choices=BUY_ORDER_STATUS, db_index=True, default=BuyOrderStatus.New)
    message = models.CharField(max_length=1024, null=True, default='')
    create_date = models.DateTimeField(default=datetime.now, db_index=True)

    first_name = models.CharField('First Name', max_length=30, null=True)
    last_name = models.CharField('Last Name', max_length=30, null=True)

    shipping_address1 = models.CharField(max_length=255, verbose_name='Address 1', null=True)
    shipping_address2 = models.CharField(max_length=255, verbose_name='Address 2', null=True, blank=True)
    shipping_city = models.CharField(max_length=100, verbose_name='City', null=True)
    shipping_state = models.CharField(max_length=2, verbose_name='State', null=True)
    shipping_county = models.CharField(max_length=100, null=True, verbose_name='County')
    shipping_zip_code = models.CharField(max_length=10, verbose_name='Zip', null=True)

    billing_first_name = models.CharField(max_length=30, null=True, verbose_name='First Name')
    billing_last_name = models.CharField(max_length=30, null=True, verbose_name='Last Name')

    billing_address1 = models.CharField(max_length=255, null=True, verbose_name='Address 1')
    billing_address2 = models.CharField(max_length=255, null=True, verbose_name='Address 2', blank=True)
    billing_city = models.CharField(max_length=100, null=True, verbose_name='City')
    billing_state = models.CharField(max_length=2, null=True, verbose_name='State')
    billing_county = models.CharField(max_length=100, null=True, verbose_name='County')
    billing_zip_code = models.CharField(max_length=10, null=True, verbose_name='Zip')

    card_type = models.CharField(max_length=32, choices=CREDIT_CARD_TYPES, null=True, editable=False)
    card_display_number = models.CharField(max_length=20, null=True, editable=False)
    card_data = BlowfishField(key=settings.BILLING_CARDS_CRYPTO_KEY, null=True, editable=False)

    applied_credits = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    discounts = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    tax = models.DecimalField(max_digits=10, decimal_places=4, null=True, default='0.0')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.0'))
    size = models.IntegerField(null=True)

    payment_transaction = models.OneToOneField('members.BillingHistory', null=True)


    @staticmethod
    def list_recent(user):
        return BuyOrder.objects.filter(user=user, create_date__gte=datetime.now()-timedelta(30))

    @staticmethod
    @transaction.commit_on_success
    def create(request, data, profile):

        order = BuyOrder(user=profile.user,
                         tax=Tax.get_value(data.get('billing_state'), data.get('billing_county')),
                         **data)
        order.save()
        order.history.create()

        for cart_item in request.cart.items.all():
            for i in xrange(cart_item.quantity): #@UnusedVariable
                item = BuyOrderItem(
                    order=order,
                    item = cart_item.item,
                    is_new = cart_item.is_new,
                    price = cart_item.get_price(request)
                )
                item.save()

        order.discounts = request.cart.get_discount_amount()
        order.recalc_total()

        available_store_credits = min(request.cart.applied_credits, profile.unlocked_store_credits)
        if available_store_credits > 0:
            total = order.get_order_total()
            if total >= available_store_credits:
                order.applied_credits = available_store_credits
            else:
                order.applied_credits = total
        order.save()
        return order

    def can_be_canceled(self):
        return self.status != BuyOrderStatus.Canceled and PackSlip.objects.filter(order=self).count() == 0

    @transaction.commit_on_success
    def cancel_order(self):
        if not self.can_be_canceled():
            return

        self.status = BuyOrderStatus.Canceled
        self.save()
        for i in self.items.all():
            i.set_status(BuyOrderItemStatus.Canceled)

        from project.members.models import TransactionStatus
        if self.payment_transaction == None or self.payment_transaction.get_refund() or self.payment_transaction.status == TransactionStatus.Canceled:
            return
        if self.payment_transaction.is_setted():
            self.payment_transaction.refund_transaction(comment='Order Canceled')
        else:
            self.payment_transaction.void_transaction()

    def order_no(self):
        return '%08d' % self.id

    def get_pay_via_display(self):
        if not self.payment_transaction:
            return ''
        if self.payment_transaction.get_debit_total():
            t = (self.payment_transaction.card_data or {}).get('type')
            if self.payment_transaction.applied_credits:
                t += ' - Credits'
            return t
        return 'Credits'

    def get_aim_description(self):
        c = 'Repeat Customer' if self.user else 'New User'
        g = set()
        for i in self.items.all():
            if i.item.is_prereleased_game():
                g.add('Pre Release')
            elif i.is_new:
                g.add('New')
            else:
                g.add('Used')
        g = ' + '.join(g)
        return ' - '.join([g, c])

    def recalc_total(self):
        total = 0
        size = 0
        for item in self.items.all():
            size += 1
            total += item.price
        self.total = total
        self.size = size
        self.save()


    def change_status(self, status, message='', save=True):
        self.status = status
        self.message = message
        self.history.create(status=status, message=message)
        if save:
            self.save()

    def __unicode__(self):
        return 'Order #%08d ($%s, %s)' % (self.id, self.total, self.user)

    def display_name(self):
        return ' '.join((self.first_name, self.last_name))

    def _format_address(self, data, prefix=None):
        k = ['address1', 'address2', 'city', 'state', 'zip']
        v = []
        for key in k:
            if prefix:
                key = '_'.join((prefix, key))
            if key in data and data[key]:
                v.append(data[key])
        return ', '.join(v)

    def get_shipping_address_data(self):
        return {
            'address1': self.shipping_address1,
            'address2': self.shipping_address2,
            'city': self.shipping_city,
            'state': self.shipping_state,
            'zip': self.shipping_zip_code,
        }

    def display_shipping_address(self):
        return self._format_address(self.get_shipping_address_data())

    def get_billing_data(self):
        return {
            'first_name': self.billing_first_name,
            'last_name': self.billing_last_name,
            'address1': self.billing_address1,
            'address2': self.billing_address2,
            'city': self.billing_city,
            'state': self.billing_state,
            'zip': self.billing_zip_code,
        }

    def get_shipping_data(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'address1': self.shipping_address1,
            'address2': self.shipping_address2,
            'city': self.shipping_city,
            'state': self.shipping_state,
            'zip': self.shipping_zip_code,
        }

    def take_charge(self, aim_data):
        charge_amount = self.get_charge_amount()
        aim_transaction_id = 0
        if charge_amount:
            try:
                aim = create_aim()

                def assert_res(res):
                    if res.response_code == 1:
                        return
                    if res.response_reason_code in [2, 3, 4]:
                        raise BuyCartCompleteException('Insufficient funds are available for this transaction.')
                    if res.avs_response == 'U':
                        raise BuyCartCompleteException('We do not accept prepaid cards.')
                    raise BuyCartCompleteException('We are unable to process you credit card at this time.')

                res = aim.authorize(charge_amount, **aim_data)
                logger.debug('Credit card preauth full amount ($%s) approved? %s', charge_amount, 'YES' if res.response_code == 1 else 'NO')
                assert_res(res)

                aim_transaction_id = res.transaction_id
                res = aim.prior_auth_capture(charge_amount, res.transaction_id)
                logger.debug('Capture full amount ($%s) approved? %s', charge_amount, 'YES' if res.response_code == 1 else 'NO')
                assert_res(res)
            except BuyCartCompleteException, e:
                msg = 'Failed to bill Shop Order #%s - %s' % (self.order_no(), e.message)
                logger.debug('Authorize.net error: %s', msg)
                self.change_status(BuyOrderStatus.Problem, e.message)
                return None
#            except Exception,e:
#                msg = 'Failed to bill Shop Order #%s - %s' % (self.order_no(), e)
#                logger.debug('Authorize.net error: %s', msg)
#                self.change_status(BuyOrderStatus.Problem, e.message)
#                return None
        return aim_transaction_id


    @transaction.commit_on_success
    def complete(self, silent=False):

        def chain_objects(o1, objects=[]):
            return itertools.chain([o1] if o1 else [], itertools.ifilter(lambda x: x != o1, objects))

        zip_code = self.shipping_zip_code
        profile = self.user.get_profile()
        logger.debug('Home DC: %s', profile.dropship)

        from project.inventory.models import Dropship
        dropships = list(chain_objects(profile.dropship, Dropship.list_by_distance(zip_code)))

        def find_dropship(item, is_new):
            for dropship in dropships:
                if dropship.is_game_available(item, is_new, for_rent=False):
                    return dropship
            return None

        self.change_status(BuyOrderStatus.Checkout)
        for order_item in self.items.all():
            if order_item.item.is_prereleased_game():
                order_item.set_status(BuyOrderItemStatus.PreOrder)
                logger.debug('Pre-order item')
                continue

            logger.debug('Processing: %s %s...', self.user, order_item.item)
            dc = find_dropship(order_item.item, order_item.is_new)
            if not dc:
                order_item.set_status(BuyOrderItemStatus.Checkout)
                logger.debug('No inventory found')
                continue

            logger.debug('Item found in: %s', dc)
            order_item.source_dc = dc
            order_item.set_status(BuyOrderItemStatus.Pending)

        if not silent:
            self.send_order_creation_confirmation_email()


    def get_order_number(self):
        return '%08d' % self.id

    def list_upc(self):
        d = []
        for i in self.items.all():
            d.append(i.item.upc)
        return d

    def get_shipping_date(self):
        for h in self.history.all().filter(status=BuyOrderStatus.Shipped):
            return h.timestamp.date()
        return self.create_date.date()


    def get_order_total(self):
        coeff = decimal.Decimal('1.0') + (self.tax or decimal.Decimal('0.0')) / decimal.Decimal('100.0')
        t = self.total * coeff - self.discounts
        return decimal.Decimal('%.2f' % t)

    def get_tax_amount(self):
        coeff = (self.tax or decimal.Decimal('0.0')) / decimal.Decimal('100.0')
        return decimal.Decimal('%.2f' % (self.total * coeff))

    def get_charge_amount(self):
        return self.get_order_total() - (self.applied_credits or decimal.Decimal('0.0'))

    def send_order_confirmation_email(self):
        mail(self.user.email, 'emails/buy_emails/order_confirmation_email.html', {
            'order': self,
            'user': self.user,
        }, subject='Gamemine Order Status - Receipt #%s' % self.get_order_number())

    def send_order_creation_confirmation_email(self):
        mail(self.user.email, 'emails/buy_emails/order_creation_confirmation_email.html', {
            'user': self.user,
        }, subject='Gamemine - Your Receipt #%s' % self.get_order_number())

    def list_genres(self):
        genres_set = set()
        for i in self.items.all():
            for g in i.item.genres.all():
                genres_set.add(g.name)
        return genres_set

    def list_names(self):
        names = []
        for i in self.items.all():
            if i.item.short_name not in names:
                names.append(i.item.short_name)
        return names

    def list_units(self):
        names = []
        units = []
        for i in self.items.all():
            if i.item.short_name not in names:
                names.append(i.item.short_name)
                units.append(1)
            else:
                units[names.index(i.item.short_name)] += 1
        return units

    def list_platforms(self):
        platforms_set = set()
        for i in self.items.all():
            platforms_set.add(i.item.category.name)
        return platforms_set

    def list_ids(self):
        ids_set = set()
        for i in self.items.all():
            ids_set.add(i.item.id)
        return ids_set


class BuyOrderItemStatus:
    New = 0
    Checkout = 1
    Pending = 2
    PreOrder = 3
    Prepared = 4

    Canceled = 5
    AutoCancel = 6
    Shipped = 7
    Delivered = 8
    Refund = 9
    Chargeback = 10


BUY_ORDER_ITEM_STATUSES = (
    (BuyOrderItemStatus.New, 'New'),
    (BuyOrderItemStatus.Checkout, 'Checkout'),
    (BuyOrderItemStatus.Pending, 'Pending'),
    (BuyOrderItemStatus.PreOrder, 'Pre Order'),
    (BuyOrderItemStatus.Prepared, 'Prepared'),
    (BuyOrderItemStatus.Canceled, 'Canceled'),
    (BuyOrderItemStatus.AutoCancel, 'Auto Cancel'),
    (BuyOrderItemStatus.Shipped, 'Shipped'),
    (BuyOrderItemStatus.Delivered, 'Delivered'),
    (BuyOrderItemStatus.Refund, 'Refund'),
    (BuyOrderItemStatus.Chargeback, 'Chargeback'),
)


class BuyOrderItem(models.Model):
    order = models.ForeignKey(BuyOrder, related_name='items')
    item = models.ForeignKey('catalog.Item', editable=False)
    is_new = models.BooleanField(default=True, db_index=True, editable=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.0'))
    status = models.IntegerField(choices=BUY_ORDER_ITEM_STATUSES, db_index=True, default=BuyOrderItemStatus.New)
    date_prepared = models.DateField(db_index=True, null=True, blank=True, editable=False)
    date_shipped = models.DateField(db_index=True, null=True, blank=True, editable=False)
    source_dc = models.ForeignKey('inventory.Dropship', null=True, blank=True)
    inventory = models.ForeignKey('inventory.Inventory', null=True, blank=True)


    def __unicode__(self):
        return '%s %s %s %s $%s' % (self.item.upc, self.item, self.item.category,
                                           'NG' if self.is_new else 'UG', self.price)

    def claims(self):
        return Claim.list(self)

    def set_status(self, status, save=True):
        self.status = status
        if save:
            self.save()

    def get_amount_instock_to_buy(self):
        return self.item.get_amount_instock_to_buy(self.is_new)

    def get_amount_from_distributor_to_buy(self):
        return self.item.get_amount_from_distributor_to_buy(self.is_new)


class BuyOrderHistory(models.Model):
    class Meta:
        ordering = ['-timestamp']

    order = models.ForeignKey(BuyOrder, related_name='history')
    timestamp = models.DateTimeField(default=datetime.now, db_index=True)
    status = models.IntegerField(choices=BUY_ORDER_STATUS, default=0)
    message = models.CharField(max_length=1024, null=True, default='')

    def __unicode__(self):
        r = '%s %s' % (self.timestamp, self.get_status_display())
        if self.message:
            r += ' (%s)' % self.message
        return r


def recal_order_total(sender, instance, created, **kwargs):
    instance.order.recalc_total()
signals.post_save.connect(recal_order_total, BuyOrderItem)


class BuyList(models.Model):
    class Meta:
        ordering = ['added']

    user = models.ForeignKey(User, null=True)
    session_id = models.CharField(max_length=50, null=True, db_index=True)
    item = models.ForeignKey('catalog.Item')
    is_new = models.BooleanField(default=True, db_index=True)
    added = models.DateTimeField(default=datetime.now)
    buy_alert = models.BooleanField(default=False)

    @staticmethod
    @transaction.commit_on_success
    def add_to_list(request, item, is_new, buy_alert=False):
        list_filter = {}
        if request.user.is_authenticated():
            list_filter['user'] = request.user
        else:
            list_filter['session_id'] = request.current_session_id

        qs = BuyList.objects.filter(item=item, is_new=is_new, **list_filter)
        if qs.count() == 0:
            BuyList(item=item, is_new=is_new, buy_alert=buy_alert, **list_filter).save()
        else:
            if buy_alert:
                for i in qs:
                    i.buy_alert = buy_alert
                    i.save()

    @staticmethod
    def get(user=None, request=None):
        filter = {}
        if request:
            if request.user.is_authenticated():
                filter['user'] = request.user
                for item in BuyList.objects.filter(user=None, session_id=request.current_session_id):
                    if BuyList.objects.filter(user=request.user, is_new=item.is_new, item=item.item).count() == 0:
                        item.user = request.user
                        item.session_id = None
                        item.save()
                    else:
                        item.delete()
            else:
                filter['session_id'] = request.current_session_id
        else:
            filter['user'] = user
        qs = BuyList.objects.filter(**filter)
        return qs

    def get_price(self):
        if self.item.release_date > datetime.now().date() + timedelta(30):
            return 0
        if self.is_new:
            if self.item.available_for_selling_n() and self.item.retail_price_new > 0:
                return self.item.retail_price_new
        else:
            if self.item.available_for_selling_u() and self.item.retail_price_used > 0:
                return self.item.retail_price_used
        return 0


class PackSlip(models.Model):
    order = models.ForeignKey(BuyOrder)
    created = models.DateField(default=datetime.now, db_index=True)
    endicia_data = JSONField(null=True)
    mail_label = models.ImageField(upload_to='labels/%Y/%m/%d', null=True)
    tracking_number = models.CharField(max_length=50, null=True)
    date_shipped = models.DateTimeField(null=True, db_index=True)
    date_delivered = models.DateTimeField(null=True, db_index=True)
    source_dc = models.ForeignKey('inventory.Dropship', null=True)
    tracking_scans = JSONField(null=True)

    @staticmethod
    def prepare_order_item(order_item):
        slip, created = PackSlip.objects.get_or_create(order=order_item.order, date_shipped=None, source_dc=order_item.source_dc) #@UnusedVariable
        return slip.add_order_item(order_item)

    def order_no(self):
        return '%08d' % self.id

    def get_subtotal(self):
        p = 0
        for i in self.items.all():
            p += i.order_item.price
        return p

    def list_items_for_print(self):
        items = list(self.items.all())
        items += [None] * (10 - len(items))
        return items

    def get_tax_rate(self):
        return self.items.all()[0].order_item.order.tax or decimal.Decimal('0.0')

    def get_tax(self):
        t = self.get_tax_rate() / 100
        return self.get_subtotal() * t

    def get_total(self):
        return self.get_subtotal() + self.get_tax()

    def add_order_item(self, order_item):
        slip_item, created = PackSlipItem.objects.get_or_create(slip=self, order_item=order_item)
        if created:
            self.mail_label = None
            self.endicia_data = None
            self.tracking_number = None
            self.save()
        return slip_item

    def get_weight(self):
        weight = decimal.Decimal('0.0')
        for item in self.items.all():
            weight += item.order_item.item.get_game_weight()
        return decimal.Decimal('%0.1f' % weight)

    def request_mail_label(self):
        if self.mail_label:
            return True, None
        endicia = Endicia(**settings.ENDICIA_CONF)
        res = endicia.get_postage_label(
            weight=self.get_weight(),
            image_format=ImageFormat.GIF,
            mail_class=MailClass.First if self.get_weight() <= decimal.Decimal('7.0') else MailClass.MediaMail,
            mailpiece_shape=MailpieceShape.Parcel,
            stealth=False,
            rubber_stamp='CUSTOMER ID: %08d\nORDER # %08d' % (self.order.user.id, self.order.id),
            services={
                'delivery_confirmation': False,
            },
            reference_id='Store',
            description='Buy Shipping Label',
            partner_customer_id='%08d' % self.order.user.id,
            partner_transaction_id='%08d' % self.id,
            to={
                'name': ' '.join((self.order.first_name, self.order.last_name)),
                'address1': self.order.shipping_address1,
                'address2': self.order.shipping_address2,
                'city': self.order.shipping_city,
                'state': self.order.shipping_state,
                'postal_code': split_zip(self.order.shipping_zip_code)[0],
                'zip4': split_zip(self.order.shipping_zip_code)[1],
                'delivery_point': '00',
            },
            frm={
                'name': 'GAMEMINE',
                'city': self.source_dc.city.upper(),
                'state': self.source_dc.state.upper(),
                'postal_code': self.source_dc.postal_code.upper(),
                'zip4': split_zip(self.source_dc.postal_code)[1].upper(),
            },
            return_address=self.source_dc.address.upper(),
            postage_price=True)
        logger.debug('Mail label requested? %s', 'YES' if res.Status == '0' else 'NO')
        logger.debug('Status: %s (%s)', res.Status, res.ErrorMessage if res.Status != '0' else 'OK')
        if res.Status == '0':
            self.endicia_data = res._dict['LabelRequestResponse']
            self.tracking_number = res.TrackingNumber

            label_file = ContentFile(base64.decodestring(res.Base64LabelImage))
#            if self.mail_label:
#                self.mail_label.delete(False)
            self.mail_label.save('%08d.gif' % self.id, label_file)
        else:
            self.endicia_data = ''
            self.tracking_number = None
#            self.mail_label.delete(True)
        return res.Status == '0', res.ErrorMessage if res.Status != '0' else 'OK'

    @transaction.commit_on_success
    def mark_as_shipped(self, date=None):
        if self.date_shipped:
            return

        from project.inventory.models import InventoryStatus

        date = date or datetime.now()
        self.date_shipped = date
        self.save()
        for item in self.items.all():
            item.order_item.status = BuyOrderItemStatus.Shipped
            item.order_item.date_shipped = self.date_shipped
            item.order_item.save()
            item.order_item.inventory.status = InventoryStatus.Sold
            item.order_item.inventory.save()
        self.order.send_order_confirmation_email()


    def __get_tracking_scan(self, data):
        codes = (
            ('-1', 'Not Found'),
            ('0', 'Found - No Status'),
            ('A', 'Logged at USPS'),
            ('I', 'Scanned in Route'),
            ('D', 'Delivered'),
            ('L', 'Notice Left for Recipient'),
            ('F', 'Forwarded to New Address'),
            ('R', 'Returned to Sender'),
            ('U', 'Undeliverable'),
            ('N', 'New Item'),
            ('X', 'Other'),
        )
        for c in codes:
            if c[0] in data:
                timestamp = data[c[0]]
                timestamp = map(int, re.split('\s|-|:', timestamp))
                timestamp = datetime(*timestamp)
                yield {'code': c[0], 'message': c[1], 'timestamp': timestamp}

    def get_mail_tracking_scan(self):
        return list(self.__get_tracking_scan(self.tracking_scans))

    def set_tracking_status(self, code):
        scans = self.tracking_scans or {}
        if code == '0' or code in scans:
            return

        if code == 'D':
            self.date_delivered = datetime.now()
        elif code == 'R':
            self.send_address_hold_restriction_email()

        scans[code] = datetime.now()
        self.tracking_scans = scans
        self.save()


    def send_order_shipped_email(self):
        mail(self.order.user.email, 'emails/buy_emails/order_shipped_email.html', {
            'order': self,
            'user': self.order.user,
            'nickname': self.order.user.username,
        }, subject='Gamemine - Order Shipped')


    def send_address_hold_restriction_email(self):
        mail(self.order.user.email, 'emails/buy_emails/address_hold_restriction_email.html', {
            'order': self,
            'user': self.order.user,
        }, subject='Account Restricted - Confirm your Mailing Address')


class PackSlipItem(models.Model):
    class Meta:
        ordering = ['added']

    slip = models.ForeignKey(PackSlip, related_name='items')
    order_item = models.OneToOneField(BuyOrderItem, related_name='pack_slip_item')
    added = models.DateTimeField(default=datetime.now, db_index=True)
