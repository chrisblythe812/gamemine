from logging import debug #@UnusedImport

from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
import decimal
import base64

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.base import ContentFile

from django_snippets.thirdparty.models.json_field import JSONField
from endiciapy.enums import ImageFormat, MailClass, MailpieceShape
from endiciapy.endicia import Endicia

from project.catalog.models import Item
from project.utils.mailer import mail


def get_shipping_cost(lbs=0, oz=0):
    sum_lbs = (16 * lbs + oz + 15) / 16
    if sum_lbs < 1:
        sum_lbs = 1
    if sum_lbs > 10:
        sum_lbs = 10
    shipping_prices = ['2.50', '3.00', '3.50', '4.00', '4.50', '5.00', '5.50', '6.00', '6.50', '7.00']
    return Decimal(shipping_prices[int(sum_lbs)-1])


def split_zip(zip):
    z = zip.split('-')
    z += ['0000'] * (2 - len(z))
    return z


class TradeCart(models.Model):
    user = models.OneToOneField(User, null=True)
    anonymous_cart_id = models.CharField(max_length=40, null=True, db_index=True)
    size = models.IntegerField(default=0)
    modified = models.DateTimeField(auto_now_add=True, auto_now=True, default=datetime.now)
    last_session_timestamp = models.DateTimeField(null=True)

    @staticmethod
    def get(request):
        if request.user.is_authenticated():
            if 'trade_cart_id' in request.session:
                cart_id = request.session['trade_cart_id']
                cart, _created = TradeCart.objects.get_or_create(anonymous_cart_id=cart_id)
                if cart.size:
                    TradeCart.objects.filter(user=request.user).delete()
                    cart.user = request.user
                    cart.anonymous_cart_id = None
                    cart.save()
                else:
                    cart.delete()
                    cart, _created = TradeCart.objects.get_or_create(user=request.user)
                del request.session['trade_cart_id']
            else:
                cart, _created = TradeCart.objects.get_or_create(user=request.user)
        else:
            if 'trade_cart_id' not in request.session:
                request.session['trade_cart_id'] = str(uuid4())
            cart_id = request.session['trade_cart_id']
            cart, _created = TradeCart.objects.get_or_create(anonymous_cart_id=cart_id)
        cart.request = request
        return cart

    def get_items(self):
        items = self.items.all()
        hot_trade_amount = 3
        for i in items:
            i.hot_trade = False
        for i in items:
            if i.item.hot_trade:
                i.hot_trade = True
                hot_trade_amount -= i.quantity
            if hot_trade_amount <= 0:
                break
        return items

    def push_item(self, request, item, quantity=1, inc_quantity=None, is_complete=True):
        try:
            cart_item = self.items.get(item=item, is_complete=is_complete)
        except TradeCartItem.DoesNotExist:
            cart_item = TradeCartItem(cart=self,
                                      item=item,
                                      user_session_id=request.current_session_id,
                                      is_complete=is_complete)
            if is_complete:
                cart_item.user_session_price = item.trade_price
            else:
                cart_item.user_session_price = item.trade_price_incomplete

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

    def _recalc_size(self):
        self.size = self.items.aggregate(models.Sum('quantity'))['quantity__sum'] or 0

class TradeCartItem(models.Model):
    class Meta:
        ordering = ['id']

    cart = models.ForeignKey(TradeCart, related_name='items')
    item = models.ForeignKey('catalog.Item')
    quantity = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True, default=datetime.now)
    user_session_id = models.CharField(max_length=40)
    user_session_price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_value(self):
        return self.user_session_price * self.quantity


class TradeOrder(models.Model):
    class Meta:
        ordering = ['-create_date']

    barcode = models.CharField(max_length=100, db_index=True, null=True)

    user = models.ForeignKey(User, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)

    first_name = models.CharField('First Name', max_length=30, null=True)
    last_name = models.CharField('Last Name', max_length=30, null=True)

    shipping_address1 = models.CharField(max_length=255, verbose_name='Address 1', null=True)
    shipping_address2 = models.CharField(max_length=255, verbose_name='Address 2', null=True, blank=True)
    shipping_city = models.CharField(max_length=100, verbose_name='City', null=True)
    shipping_state = models.CharField(max_length=2, verbose_name='State', null=True)
    shipping_county = models.CharField(max_length=100, verbose_name='County', null=True)
    shipping_zip_code = models.CharField(max_length=10, verbose_name='Zip', null=True)

    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    size = models.IntegerField(null=True)

    received_date = models.DateTimeField(db_index=True, null=True, blank=True)

    @staticmethod
    def create(request, cart):
        cart_items = cart.get_items()
        total_amount = sum([item.quantity * item.user_session_price for item in cart_items])

        order = TradeOrder(
            user = request.user,
            first_name = request.user.first_name,
            last_name = request.user.last_name,
            shipping_address1 = request.user.profile.shipping_address1,
            shipping_address2 = request.user.profile.shipping_address2,
            shipping_city = request.user.profile.shipping_city,
            shipping_state = request.user.profile.shipping_state,
            shipping_zip_code = request.user.profile.shipping_zip,
            total = total_amount,
            size = sum(map(lambda x: x.quantity, cart_items)),
        )
        order.save()

        hot_trades = []
        for item in cart_items:
            for _i in xrange(item.quantity):
                order_item = TradeOrderItem()
                order_item.order = order
                order_item.item = item.item
                order_item.is_complete = item.is_complete
                order_item.price = item.user_session_price
                order_item.save()
                if item.hot_trade:
                    hot_trades.append(order_item)
        if len(hot_trades) >= 3:
            hot_trades = hot_trades[:3]
            p = 0
            for i in hot_trades:
                i.hot_trade = True
                p += i.price
                i.save()
            order.bonus = p * decimal.Decimal('0.25')
            order.save()

        cart.delete()
        return order

    def get_order_total(self):
        return self.total + (self.bonus or 0) + self.get_shipping_cost()

    def order_no(self):
        return self.get_order_number()
    order_no.short_description = 'Order Number'

    def __unicode__(self):
        return self.order_no()

    def get_mailing_date(self):
        return self.create_date + timedelta(7)

    def get_received_date(self):
        if self.received_date:
            return self.received_date.strftime('%x')
        else:
            return ''
    get_received_date.short_description = 'Received date'

    def get_order_number(self):
        if self.barcode:
            return self.barcode

        from random import Random
        r = Random()
        r.seed(self.id)
        result = ''
        for c in '%07d' % self.id:
            result += '%d%c' % (r.randrange(10), c)
        result = 'GT1-' + result[:7] + '-' + result[7:]
        return result

    def claims(self):
        for i in self.items.all():
            for c in i.claims():
                yield c

    def get_create_date(self):
        return self.create_date.strftime('%x')

    def get_fullname(self):
        return (self.first_name + ' ' + self.last_name).strip()
    get_fullname.short_description = 'Member'

    def is_processed(self):
        for item in self.items.all():
            if not item.processed:
                return False
        return True

    def groupped_items(self):
        items = []
        for o in self.items.values('item_id').annotate(qty=models.Count('item'), val=models.Sum('price')).order_by():
            o['item'] = Item.objects.get(id=o['item_id'])
            items.append(o)
        return items

    #
    # e-mails
    #
    def send_order_confirmation(self):
        mail(self.user.email, 'emails/trade_emails/order_confirmation.html', {
            'order': self,
            'user': self.user,
        }, subject='Gamemine Trade-In - Confirmation #' + self.order_no())

    def send_order_processed(self):
        mail(self.user.email, 'emails/trade_emails/order_processed.html', {
            'order': self,
            'user': self.user,
        }, subject='Gamemine Trade-In Order #' + self.order_no() + ' Processed')

    def send_order_expired(self):
        mail(self.user.email, 'emails/trade_emails/order_expired.html', {
            'order': self,
            'user': self.user,
            'items': self.groupped_items(),
        }, subject='Gamemine Trade-In #' + self.order_no() + ' Has Expired')

    def get_shipping_cost(self):
        return self.get_shipping_reimbursements()

    def get_shipping_reimbursements(self):
        amount = 0
        for item in self.items.all():
            amount += item.get_shipping_reimbursements()
        return amount

    def get_expiration_date(self):
        return self.create_date + timedelta(30)


def trade_order_post_save(sender, instance, created, **kwargs):
    if created:
        instance.barcode = instance.get_order_number()
        instance.save()
post_save.connect(trade_order_post_save, TradeOrder)

class TradeOrderItem(models.Model):
    class Meta:
        ordering = ['id']

    order = models.ForeignKey(TradeOrder, related_name='items')
    item = models.ForeignKey('catalog.Item', editable=False, related_name='trade_items')
    original_item = models.ForeignKey('catalog.Item', editable=False, related_name='original_trade_items', null=True)

    is_complete = models.BooleanField(default=False, db_index=True)

    is_match = models.BooleanField(default=False, db_index=True)
    is_damaged = models.BooleanField(default=False, db_index=True)

    is_exellent = models.BooleanField(default=False, db_index=True)
    is_like_new = models.BooleanField(default=False, db_index=True)
    is_very_good = models.BooleanField(default=False, db_index=True)
    is_factory_sealed = models.BooleanField(default=False, db_index=True)

    is_broken = models.BooleanField(default=False, db_index=True)
    is_unplayable = models.BooleanField(default=False, db_index=True)
    is_lightly_scratched = models.BooleanField(default=False, db_index=True)
    is_heavily_scratched = models.BooleanField(default=False, db_index=True)

    is_refurblished = models.BooleanField(default=False, db_index=True)
    is_mailback = models.BooleanField(default=False, db_index=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    processed = models.BooleanField(default=False, db_index=True)
    processed_date = models.DateTimeField(null=True, db_index=True)
    processed_by = models.ForeignKey(User, null=True, related_name='processed_trade_items')

    declined = models.BooleanField(default=False)

    returning_endicia_data = JSONField(null=True, editable=False)
    returning_mail_label = models.ImageField(upload_to='labels/%Y/%m/%d', null=True, editable=False)
    returning_date = models.DateTimeField(null=True)
    returning_by = models.ForeignKey(User, null=True, related_name='returning_trade_items')

    inventory = models.OneToOneField('inventory.Inventory', null=True, related_name='trade_item')
    bastard_flag = models.BooleanField(default=False)

    hot_trade = models.BooleanField(default=False)


    def __unicode__(self):
        return unicode(self.item)

    def get_total(self):
        return self.price

    def claims(self):
        from project.claims.models import Claim
        return Claim.list(self)

    def get_decline_reason(self):
        return 'Damage'
#        r = []
#        if self.is_damaged:
#            r.append('Damaged')
#            if self.is_refurblished:
#                r.append('Needs Repair')
#        if self.is_broken:
#            r.append('Broken')
#        if self.is_like_new:
#            r.append('Like New')
#        if self.is_very_good:
#            r.append('Very Good')
#        if self.is_factory_sealed:
#            r.append('Factory Sealed')
#        if self.is_unplayable:
#            r.append('Unplayable')
#        if self.is_lightly_scratched:
#            r.append('Lightly Scratched')
#        if self.is_heavily_scratched:
#            r.append('Heavily Scratched')
#        return ', '.join(r)

    def get_comments(self):
        if self.processed:
            if self.declined:
                s = u'Declined'
            else:
                s = u'Accepted'
            if self.is_damaged:
                s += u' - Damaged'
                if self.is_refurblished:
                    s += u' - Needs Repair'
            if self.is_exellent:
                s += u' - Exellent'
            if self.is_broken:
                s += u' - Broken'
            if self.is_like_new:
                s += u' - Like New'
            if self.is_very_good:
                s += u' - Very Good'
            if self.is_factory_sealed:
                s += u' - Factory Sealed'
            if self.is_unplayable:
                s += u' - Unplayable'
            if self.is_lightly_scratched:
                s += u' - Lightly Scratched'
            if self.is_heavily_scratched:
                s += u' - Heavily Scratched'
            return s
        else:
            return u'Pending'

    def get_weight(self):
        return self.item.get_game_weight()

    def get_shipping_reimbursements(self):
        return min(get_shipping_cost(oz=self.get_weight()) + 1, self.price / 10)

    def request_returning_label(self):
        if self.returning_mail_label:
            return True, None
        endicia = Endicia(**settings.ENDICIA_CONF)
        res = endicia.get_postage_label(
            weight=self.get_weight(),
            image_format=ImageFormat.GIF,
            mail_class=MailClass.First if self.get_weight() <= decimal.Decimal('7.0') else MailClass.MediaMail,
            mailpiece_shape=MailpieceShape.Parcel,
            stealth=False,
            rubber_stamp='CUSTOMER ID: %08d\nORDER # %s' % (self.order.user.id, self.order.order_no()),
            services={
                'delivery_confirmation': False,
            },
            reference_id='Trade',
            description='Trade Returning Label',
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
                'city': 'Delray Beach',
                'state': 'FL',
                'postal_code': '33482',
                'zip4': '9901',
            },
            return_address='P.O. Box 6487',
            postage_price=True)
        if res.Status == '0':
            self.returning_endicia_data = res._dict['LabelRequestResponse']

            label_file = ContentFile(base64.decodestring(res.Base64LabelImage))
            if self.returning_mail_label:
                self.returning_mail_label.delete(False)
            self.returning_mail_label.save('%08d.gif' % self.id, label_file)
        else:
            self.returning_endicia_data = ''
        return res.Status == '0', res.ErrorMessage if res.Status != '0' else 'OK'

    def get_price_with_bonus(self):
        return self.price + self.get_shipping_reimbursements()


class TradeListItem(models.Model):
    class Meta:
        ordering = ['id']

    user = models.ForeignKey(User, null=True, related_name='tradelist')
    session_id = models.CharField(max_length=50, null=True, db_index=True)
    item = models.ForeignKey('catalog.Item', related_name='items')
    is_complete = models.BooleanField(default=True, db_index=True)
    added = models.DateTimeField(auto_now_add=True, default=datetime.now)

    @staticmethod
    def add(request, item, is_complete):
        list_filter = {'item': item}
        if request.user.is_authenticated():
            list_filter['user'] = request.user
        else:
            list_filter['session_id'] = request.current_session_id
        item, _created = TradeListItem.objects.get_or_create(**list_filter)
        item.is_complete = is_complete
        item.save()
        return item


    @staticmethod
    def get(request):
        filter = {}
        if request.user.is_authenticated():
            filter['user'] = request.user
            for item in TradeListItem.objects.filter(user=None, session_id=request.current_session_id):
                if TradeListItem.objects.filter(user=request.user, item=item.item).count() == 0:
                    item.user = request.user
                    item.session_id = None
                    item.save()
                else:
                    item.delete()
        else:
            filter['session_id'] = request.current_session_id
        qs = TradeListItem.objects.filter(**filter)
        return qs

    @staticmethod
    def get_for_user(user):
        qs = TradeListItem.objects.filter(user=user)
        return qs

    def get_price(self):
        if self.is_complete:
            return self.item.trade_price
        else:
            return self.item.trade_price_incomplete
