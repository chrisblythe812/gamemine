import logging
from uuid import uuid4
import datetime
from dateutil.relativedelta import relativedelta
from hashlib import md5
import decimal

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django_snippets.models import BlowfishField
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from project.trade.models import TradeOrderItem
from project.utils.mailer import mail
from project.utils import create_aim
from django.utils.safestring import mark_safe
from authorizenet.response import AimResponse

logger = logging.getLogger(__name__)


CREDIT_CARD_TYPES = (
    ('visa', 'Visa'),
    ('master-card', 'Master Card'),
    ('american-express', 'American Express'),
    ('discover', 'Discover'),
)

ACCOUNT_STATUSES = (
    (0, 'Active'),
    (1, 'Restricted'),
    (2, 'Suspended'),
)

PARENTAL_CONTROL = (
    (0, 'Allow Access to All Games'),
    (1, 'Allow E, EC Only'),
    (2, 'Allow E10+, E, EC Only'),
    (3, 'Allow T, E10+, E, EC Only'),
    (4, 'Allow EC Only'),
)

PARENTAL_CONTROL_REVIEWS = (
    (0, 'Allow Reading/Writing All User Reviews'),
    (1, 'Allow Reading User Reviews Only'),
    (2, 'Allow Reading/Writing User Reviews Bases on My Game and Movie Settings'),
)

HOW_DID_YOU_HEAR_CHOICES = (
    (1, 'Web'),
    (2, 'Radio'),
    (3, 'Magazine Ad'),
    (4, 'TV'),
    (5, 'Friend'),
    (6, 'Web Ad/Link'),
    (7, 'Web Search'),
    (8, 'News Article'),
    (9, 'GameSpot'),
)


def get_avatar_upload_to(instance, filename, suffix=None):
    id = instance.user.id
    ext = suffix or filename.split('.')[-1]
    return 'users/%d/%d.%s' % (id % 1000, id, ext)


class ProfileEntryPoint:
    Imported = 0
    Direct = 1
    Buy = 2
    Trade = 3
    Rent = 4
    DeckTheHalls = 5

ENTRY_POINTS = (
    (ProfileEntryPoint.Imported, 'Imported'),
    (ProfileEntryPoint.Direct, 'Direct'),
    (ProfileEntryPoint.Buy, 'Buy'),
    (ProfileEntryPoint.Trade, 'Trade'),
    (ProfileEntryPoint.Rent, 'Rent'),
    (ProfileEntryPoint.DeckTheHalls, 'Deck the Halls'),
)


class Group:
    Customer = 0
    PurchaseManager = 1
    DC_Operator = 2
    DC_Manager = 3
    CS_Agent = 4
    CS_Manager = 5
    Accounting = 6
    Executive = 7

    All = 100


GROUPS = (
    (Group.Customer, 'Customer'),
    (Group.PurchaseManager, 'Purchase Manager'),
    (Group.DC_Operator, 'DC Operator'),
    (Group.DC_Manager, 'DC Manager'),
    (Group.CS_Agent, 'CS Agent'),
    (Group.CS_Manager, 'CS Manager'),
    (Group.Accounting, 'Accounting'),
    (Group.Executive, 'Executive'),
)


class Campaign(models.Model):
    cid = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['cid']

    @staticmethod
    def get_title(cid):
        try:
            return Campaign.objects.get(cid=cid).name
        except Campaign.DoesNotExist:
            return cid


class ProfileManager(models.Manager):
    def build_and_create(self, **kwargs):
        # This is deprecated method
        # this logic moved to save() method
        shipping_data = kwargs.pop("shipping_data")
        billing_data = kwargs.pop("billing_data", None)
        billing_card_data = kwargs.pop("billing_card_data", None)

        if "user" not in kwargs:
            user = User(
                username=kwargs.pop("username"),
                first_name=shipping_data["first_name"],
                last_name=shipping_data["last_name"],
                email=kwargs.pop("email")
            )
            user.set_password(kwargs.pop("password"))
            user.save()
        else:
            user = kwargs.pop("user")

        profile = self.model(
            user=user,
            activation_code=str(uuid4()),
            **kwargs
        )
        profile.set_shipping_address_data(shipping_data, save=False)
        if billing_card_data:
            profile.set_billing_name_data(billing_data, save=False)
            profile.set_billing_address_data(billing_data, save=False)
            profile.set_billing_card_data(billing_card_data, save=True)
        profile.save()

        return profile


class Profile(models.Model):
    user = models.OneToOneField(User, editable=False, null=True)  # null=True is required for checkout! --pashka
    group = models.IntegerField(choices=GROUPS, default=Group.Customer)

    activation_code = models.CharField(max_length=50, db_index=True, null=True)
    campaign_cid = models.CharField(max_length=255, null=True, db_index=True)
    sid = models.CharField(max_length=255, null=True, db_index=True)
    affiliate = models.CharField(max_length=255, null=True, db_index=True, blank=True)

    account_status = models.IntegerField(choices=ACCOUNT_STATUSES, default=0)

    shipping_address1 = models.CharField(max_length=255, null=True, verbose_name='Address 1')
    shipping_address2 = models.CharField(max_length=255, null=True, verbose_name='Address 2', blank=True)
    shipping_city = models.CharField(max_length=100, null=True, verbose_name='City')
    shipping_county = models.CharField(max_length=100, null=True, verbose_name='County')
    shipping_state = models.CharField(max_length=2, null=True, verbose_name='State')
    shipping_zip = models.CharField(max_length=10, null=True, verbose_name='Zip')
    shipping_checksum = models.CharField(max_length=50, null=True, db_index=True)

    phone = models.CharField(max_length=100, null=True, verbose_name='Phone', blank=True)

    store_credits = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    bonus_store_credits = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    locked_store_credits = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    pending_credits = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))

    owned_systems = models.ManyToManyField('catalog.Category')
    favorite_genres = models.ManyToManyField('catalog.Genre')

    how_did_you_hear = models.IntegerField(choices=HOW_DID_YOU_HEAR_CHOICES, null=True, db_index=True)
    parental_control = models.IntegerField(choices=PARENTAL_CONTROL, default=0)
    parental_control_reviews = models.IntegerField(choices=PARENTAL_CONTROL_REVIEWS, default=0)

    avatar = models.ImageField(upload_to=get_avatar_upload_to, null=True)
    entry_point = models.IntegerField(choices=ENTRY_POINTS, default=ProfileEntryPoint.Imported, db_index=True)

    dropship = models.ForeignKey('inventory.Dropship', null=True, related_name='members')
    dc = models.ForeignKey('inventory.Dropship', null=True, blank=True, related_name='employees')

    extra_rent_slots = models.IntegerField(default=0)
    strikes = models.IntegerField(default=0)

    rent_pixels_flag = models.BooleanField(default=False)

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    objects = ProfileManager()

    @staticmethod
    def create(request, user, **kwargs):
        return Profile(user=user,
                       campaign_cid=str(request.campaign_id),
                       sid=str(request.sid),
                       affiliate=str(request.affiliate),
                       activation_code=str(uuid4()),
                       **kwargs)

    def __unicode__(self):
        return self.user.first_name or self.user.username

    def check_rent_pixels(self):
        """
        This method triggered from "pixels.html" template, sets rent_pixels_flag

        For compatibility only, it's a bad practice to set anything from template
        """

        self.rent_pixels_flag = True
        self.save()
        logger.debug('RENT PIXELS: TRUE, %s', self.campaign_cid)
        return True

    def inc_strikes(self, amount=1, silent=False):
        self.strikes += amount
        if self.strikes > 3:
            self.strikes = 3
        elif self.strikes < 0:
            self.strikes = 0
        self.save()
        if self.strikes == 3:
            if not silent:
                self.suspend_rent_account()
        else:
            from project.rent.models import MemberRentalPlan, RentalPlanStatus
            plan = MemberRentalPlan.get_current_plan(self.user)
            if plan and plan.status == RentalPlanStatus.Suspended:
                plan.status = RentalPlanStatus.Active if plan.payment_fails_count == 0 else RentalPlanStatus.Delinquent
                plan.save()

    def suspend_rent_account(self):
        from project.rent.models import MemberRentalPlan

        plan = MemberRentalPlan.get_current_plan(self.user)
        if plan:
            plan.suspend_plan()

    def get_rental_status(self, exclude_canceled=True):
        from project.rent.models import MemberRentalPlan
        plan = MemberRentalPlan.get_current_plan(self.user, exclude_canceled)
        return plan.get_status_display() if plan else 'No rental plan'

    def is_rental_active(self):
        from project.rent.models import MemberRentalPlan
        plan = MemberRentalPlan.get_current_plan(self.user)
        if plan:
            return True
        return False

    def get_campaign_cid_display(self):
        if self.campaign_cid is None or self.campaign_cid == u'':
            return u"Gamemine Direct"
        try:
            return Campaign.objects.get(pk=self.campaign_cid).name
        except:
            return u"Unknown Campaign"

    def get_icon_url(self):
        return self.avatar.url if self.avatar else settings.STATIC_URL + 'user.jpg'

    def get_full_name(self):
        u = self.user
        return ' '.join([u.first_name, u.last_name]).strip()

    def get_name_display(self):
        return self.get_full_name() or self.user.username

    def get_name_data(self):
        return {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }

    def set_name_data(self, data, save=True):
        self.user.first_name = data.get('first_name')
        self.user.last_name = data.get('last_name')
        if save:
            self.user.save()

    def has_shipping_address(self):
        return True if self.shipping_address1 else False

    def get_shipping_address_data(self, prefix=''):
        prefix = prefix + '_' if prefix else ''
        return {
            prefix + 'address1': self.shipping_address1,
            prefix + 'address2': self.shipping_address2,
            prefix + 'city': self.shipping_city,
            prefix + 'state': self.shipping_state,
            prefix + 'county': self.shipping_county,
            prefix + 'zip_code': self.shipping_zip,
        }

    def set_shipping_address_data(self, data, save=True):
        self.shipping_address1 = data.get('address1')
        self.shipping_address2 = data.get('address2')
        self.shipping_city = data.get('city')
        self.shipping_state = data.get('state')
        self.shipping_county = data.get('county')
        self.shipping_zip = data.get('zip_code')
        self.calc_shipping_checksum(False)
        self.link_to_dropship(dropship=None, save=False)
        if save:
            self.save()

    def calc_shipping_checksum(self, save=True):
        if not self.shipping_address1:
            self.shipping_checksum = None
        else:
            d = '\n'.join([
                self.shipping_address1 or '',
                self.shipping_address2 or '',
                self.shipping_city or '',
                self.shipping_state or '',
                self.shipping_zip or '',
            ])
            m = md5()
            m.update(d)
            self.shipping_checksum = m.hexdigest()
        if save:
            self.save()

    def get_shipping_data(self):
        return reduce(lambda a, b: b.update(a) or b, [
            self.get_name_data(),
            self.get_shipping_address_data(),
        ], {})

    def get_payment_card(self):
        if not hasattr(self, '_cached_card'):
            card, _created = BillingCard.objects.get_or_create(user=self.user)
            self._cached_card = card
        return self._cached_card

    def get_billing_name_data(self):
        card = self.get_payment_card()
        return {
            'first_name': card.first_name,
            'last_name': card.last_name,
        }

    def set_billing_name_data(self, data, save=True):
        card = self.get_payment_card()
        card.first_name = data.get('first_name')
        card.last_name = data.get('last_name')
        if save:
            card.save()

    def get_billing_address_data(self):
        card = self.get_payment_card()
        return {
            'address1': card.address1,
            'address2': card.address2,
            'city': card.city,
            'state': card.state,
            'county': card.county,
            'zip_code': card.zip,
        }

    def set_billing_address_data(self, data, save=True):
        card = self.get_payment_card()
        card.address1 = data.get('address1')
        card.address2 = data.get('address2')
        card.city = data.get('city')
        card.state = data.get('state')
        card.county = data.get('county')
        card.zip = data.get('zip_code')
        if save:
            card.save()

    def get_billing_data(self):
        return reduce(lambda a, b: b.update(a) or b, [
            self.get_billing_name_data(),
            self.get_billing_address_data(),
        ], {})

    def get_billing_card_data(self):
        card = self.get_payment_card()
        r = {
            'type': card.type,
        }
        r.update(card.data or {
            'number': None,
            'exp_year': None,
            'exp_month': None,
            'code': None,
        })
        return r

    def set_billing_card_data(self, data, save=True):
        from project.rent.models import MemberRentalPlan, RentalPlanStatus
        card = self.get_payment_card()
        card.type = data.get('type')
        card.data = {
            'number': data.get('number'),
            'exp_year': data.get('exp_year'),
            'exp_month': data.get('exp_month'),
            'code': data.get('code'),
        }
        card.update_display_number()
        rent_plan = MemberRentalPlan.get_current_plan(self.user)
        if rent_plan and rent_plan.status == RentalPlanStatus.AutoCanceled:
            rent_plan.delinquent_next_check = datetime.date.today()
            rent_plan.set_status(RentalPlanStatus.Delinquent)
        if save:
            card.save()

    def get_billing_card_display(self):
        card = self.get_payment_card()
        return card.display_number

    def add_bonus_store_credits(self, amount, save=True):
        if not amount:
            return
        self.store_credits += amount
        self.bonus_store_credits += amount
        self.locked_store_credits += amount
        if save:
            self.save()

    def clear_locked_store_credits(self, save=True):
        self.locked_store_credits = 0
        if save:
            self.save()

    def get_cashable_credits(self):
        return self.unlocked_store_credits - (self.bonus_store_credits or decimal.Decimal('0.0'))

    @property
    def unlocked_store_credits(self):
        return (self.store_credits or decimal.Decimal('0.0')) - (self.locked_store_credits or decimal.Decimal('0.0'))

    def withdraw_store_credits(self, amount, save=True, force=False):
        if not amount:
            return
        if not force and self.unlocked_store_credits < amount:
            raise Exception('Not enough store credits to withdraw.')
        if self.bonus_store_credits >= amount:
            self.bonus_store_credits -= amount
        else:
            self.bonus_store_credits = decimal.Decimal('0.0')
        self.store_credits -= amount
        if save:
            self.save()

    def has_game_perks(self):
        # TODO: implement me please
        return False

    def get_pending_credits(self):
#        return TradeOrderItem.objects.filter(processed=False, order__user=self.user).aggregate(models.Sum('price'))['price__sum']
        r = 0
        for i in TradeOrderItem.objects.filter(processed=False, order__user=self.user):
            r += i.price + i.get_shipping_reimbursements()
        return r

    def send_email_confirmation_mail(self):
        self.activation_code = str(uuid4())
        self.save()
        url = 'http://%s%s' % (
            Site.objects.get_current().domain,
            reverse('members:confirm_registration', args=[self.activation_code]))
        terms_url = 'http://%s%s' % (
            Site.objects.get_current().domain,
            reverse('simple-page', args=['Terms']))
        mail(self.user.email, 'emails/account_emails/email_confirmation.html', {
            'user': self.user,
            'email': self.user.email,
            'url': url,
            'terms_url': terms_url,
        }, subject='Gamemine - Please Confirm your Email Address')

    def send_edit_account_information_mail(self, changed_info):
        mail(self.user.email, 'emails/account_emails/edit_account_information.html', {
            'user': self.user,
            'changed_info': changed_info,
        }, subject='Gamemine - Account Update Confirmation')

    def send_membership_suspension_mail(self):
        mail(self.user.email, 'emails/account_emails/membership_suspension.html', {
            'user': self.user,
        }, subject='Your Gamemine Account')

    def suspend_account(self):
        self.user.is_active = False
        self.user.save()
        self.send_membership_suspension_mail()

    def get_owned_systems(self):
        if self.owned_systems.all().count() == 0:
            from project.catalog.models.categories import Category
            return Category.list()
        return self.owned_systems.all()

    def get_favorite_genres(self):
        if self.favorite_genres.all().count() == 0:
            from project.catalog.models.categories import Genre
            return Genre.objects.all()
        return self.favorite_genres.all()

    def link_to_dropship(self, dropship=None, save=True):
        from project.inventory.models import Dropship
        self.dropship = dropship or Dropship.find_closest(self.shipping_zip)
        if save:
            self.save()

    def block_account(self):
        self.activation_code = None
        self.save()
        self.user.is_active = False
        self.user.save()

    def unblock_account(self):
        self.user.is_active = True
        self.user.save()


class BillingCard(models.Model):
    user = models.OneToOneField(User)

    type = models.CharField(max_length=32, choices=CREDIT_CARD_TYPES, null=True)
    display_number = models.CharField(max_length=20, null=True)
    data = BlowfishField(key=settings.BILLING_CARDS_CRYPTO_KEY, null=True)

    first_name = models.CharField('First Name', max_length=30, null=True, blank=True)
    last_name = models.CharField('Last Name', max_length=30, null=True, blank=True)

    address1 = models.CharField(max_length=255, null=True, verbose_name='Address 1')
    address2 = models.CharField(max_length=255, null=True, blank=True, verbose_name='Address 2')
    city = models.CharField(max_length=100, null=True, verbose_name='City')
    state = models.CharField(max_length=2, null=True, verbose_name='State')
    county = models.CharField(max_length=100, null=True, blank=True, verbose_name='County')
    zip = models.CharField(max_length=10, null=True, verbose_name='Zip')

    checksum = models.CharField(max_length=64, db_index=True, null=True)
    address_checksum = models.CharField(max_length=64, db_index=True, null=True)

    def is_expired(self):
        exp_date = datetime.date(
            int(p.billing_card.data['exp_year']),
            int(p.billing_card.data['exp_month']),
            1
        ) + relativedelta(months=1)
        today = datetime.date.today()
        return today >= exp_date

    def update_display_number(self):
        number = (self.data or {}).get('number')
        if number:
            last_digits = number[-4:]
            self.display_number = 'XXXX-XXXX-XXXX-' + last_digits
        else:
            self.display_number = None

    def save(self, *args, **kwargs):
        self.update_display_number()
        number = (self.data or {}).get('number')
        if number:
            m = md5()
            m.update(number or '')
            self.checksum = m.hexdigest()
        else:
            self.checksum = ''
        if self.address1:
            m = md5()
            m.update('\n'.join((self.address1 or '', self.city or '', self.state or '')))
            self.address_checksum = m.hexdigest()
        else:
            self.address_checksum = ''
        super(BillingCard, self).save(*args, **kwargs)

    @staticmethod
    def get(user):
        for card in BillingCard.objects.filter(user=user):
            return card
        return None


PAYMENT_REASON = (
    ('buy', 'Buy'),
    ('trade', 'Trade'),
    ('rent', 'Rent'),
)


class TransactionStatus:
    Passed = 0
    Declined = 1
    Unknown = 2
    Authorized = 3
    Canceled = 4
    Mistaken = 5


BILLING_HISTORY_STATUSES = (
    (TransactionStatus.Passed, 'Passed'),
    (TransactionStatus.Authorized, 'Authorized'),
    (TransactionStatus.Declined, 'Declined'),
    (TransactionStatus.Unknown, 'Unknown'),
    (TransactionStatus.Canceled, 'Canceled'),
    (TransactionStatus.Mistaken, 'Mistaken'),
)


class TransactionType:
    Unknown = 0
    RentPayment = 1
    TradePayment = 2
    BuyCheckout = 3

TRANSACTION_TYPES = (
    (TransactionType.Unknown, 'Unknown'),
    (TransactionType.RentPayment, 'Rental plan payment'),
    (TransactionType.TradePayment, 'Trade payment'),
    (TransactionType.BuyCheckout, 'Buy checkout'),
)


class BillingHistory(models.Model):
    class Meta:
        ordering=['-timestamp']

    user = models.ForeignKey(User, null=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    payment_method = models.CharField(max_length=50, null=True)
    description = models.CharField(max_length=512)

    credit = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    debit = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=decimal.Decimal('0.0'))

    tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    applied_credits = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=decimal.Decimal('0.0'))

    reason = models.CharField(max_length=32, choices=PAYMENT_REASON, null=True)
    status = models.IntegerField(choices=BILLING_HISTORY_STATUSES, default=TransactionStatus.Passed,
                                 db_index=True)
    type = models.IntegerField(choices=TRANSACTION_TYPES, default=TransactionType.Unknown,
                               db_index=True)
    aim_transaction_id = models.CharField(max_length=50, null=True)
    setted = models.BooleanField(default=True)
    card_data = BlowfishField(key=settings.BILLING_CARDS_CRYPTO_KEY, null=True)
    refered_transaction = models.ForeignKey('BillingHistory', null=True)

    message = models.CharField(max_length=1024, null=True)
    aim_response = BlowfishField(key=settings.BILLING_CARDS_CRYPTO_KEY, null=True)

    def __unicode__(self):
        return "%s | %s | %s | $%s" % (
            self.user, self.description, self.get_status_display(), self.debit
        )

    def get_debit_total(self):
        return self.get_net_debit() + (self.tax or decimal.Decimal('0.00')) - (self.applied_credits or decimal.Decimal('0.0'))

    def get_net_debit(self):
        if self.type == TransactionType.RentPayment:
            return self.debit
        else:
            return self.debit - (self.tax or decimal.Decimal('0.0'))

    def status_display(self):
        if self.get_refund():
            return 'Refund'
        return self.get_status_display()

    @staticmethod
    def log(user, payment_method, description, debit=None, credit=None, reason=None, tax=None,
            status=TransactionStatus.Unknown, type=TransactionType.Unknown):
        BillingHistory(user=user, payment_method=payment_method, description=description,
                       credit=credit, debit=debit, tax=tax, reason=reason, status=status,
                       type=type).save()

    @staticmethod
    def create(user, payment_method, description='', debit=None, credit=None, reason=None,
            status=TransactionStatus.Passed, type=TransactionType.Unknown):
        r = BillingHistory(user=user, payment_method=payment_method, description=description,
                       credit=credit, debit=debit, reason=reason, status=status,
                       type=type)
        r.save()
        return r

    @staticmethod
    def get_store_gredits(user):
        return BillingHistory.objects.filter(user=user, type=TransactionType.TradePayment,
                                             status=TransactionStatus.Passed).exclude(credit=decimal.Decimal('0'))

    def is_passed(self):
        return self.status == TransactionStatus.Passed

    def refundable(self):
        return self.is_passed() and self.get_refund() == None and self.aim_transaction_id != None

    def get_refund(self):
        try:
            return Refund.objects.get(payment=self)
        except:
            return None

    def refund_transaction(self, amount=None, comment=None):
        if self.status != TransactionStatus.Passed:
            logger.debug("Warning: Transaction is NOT PASSED not found. Can't refund.")
            return None

        if not self.aim_transaction_id:
            logger.debug("Warning: Transaction ID not found. Can't refund.")
            return None

        amount = amount or self.get_debit_total()
        profile = self.user.get_profile()
        billing = profile.get_billing_data()
        shipping = profile.get_shipping_data()
        aim_data = {
            'x_email': self.user.email,
            'x_cust_id': self.user.id,
        }

        aim = create_aim()
        if self.card_data:
            cc = self.card_data['number'][-4:]
        else:
            cc = self.payment_method[-4:]
        res = aim.refund(self.aim_transaction_id, amount, cc, billing, shipping, **aim_data)
        if res.response_code != 1:
            logger.debug("Error: Can't refund.")
            return res
        profile.store_credits += self.applied_credits
        profile.save()
        refund = Refund(payment=self, amount=amount, comment=comment,
                        aim_transaction_id=res.transaction_id)
        refund.save()
        return res

    def void_transaction(self):
        aim = create_aim()
        res = aim.void(self.aim_transaction_id, {})
        if res.response_code == 1:
            profile = self.user.get_profile()
            profile.store_credits += self.applied_credits
            profile.save()

            logger.debug('Transaction was voided')
            self.status = TransactionStatus.Canceled
            self.save()
        else:
            logger.debug('Transaction was FAILED to void')


    def payment_method_display2(self):
        if self.payment_method == 'Store Credits':
            return mark_safe('Store&nbsp;Credits')
        r = ('XXXX%s %s' % (self.payment_method[-4:], (self.card_data or {}).get('type') or '')).strip()
        return mark_safe(r.replace(' ', '&nbsp;'))

    def get_name_display(self):
        if self.user:
            return self.user.get_profile().get_name_display()
        else:
            return "%s %s" % (self.aim_response["first_name"], self.aim_response["last_name"])

    def get_aim_response_display(self):
        if self.aim_response:
            for k in AimResponse.format(self.aim_response):
                yield k[0], k[1]

    def is_setted(self):
        if self.status == TransactionStatus.Passed:
            return True
        if self.status != TransactionStatus.Authorized:
            return False
        if BillingHistory.objects.filter(refered_transaction=self, status=TransactionStatus.Passed).count():
            return True
        return False

    def capture(self):
        if self.status != TransactionStatus.Authorized:
            return None

        try:
            return BillingHistory.objects.get(refered_transaction=self, status=TransactionStatus.Passed)
        except BillingHistory.DoesNotExist:
            pass

        aim = create_aim()
        profile = self.user.get_profile()
        aim_data = {
            'x_email': self.user.email,
            'x_cust_id': self.user.id,
        }
        res = aim.prior_auth_capture(self.get_debit_total(),
                                     self.aim_transaction_id,
                                     profile.get_billing_data(),
                                     profile.get_shipping_data(),
                                     **aim_data)

        success = True
        status = TransactionStatus.Passed

        if res.response_code != 1:
            success = False
            status = TransactionStatus.Declined

        billing_history = BillingHistory(user=self.user,
                                         payment_method=self.payment_method,
                                         description=self.description,
                                         debit=self.debit,
                                         reason=self.reason,
                                         type=self.type,
                                         card_data=self.card_data,
                                         tax=self.tax,
                                         refered_transaction=self,
                                         status=status,
                                         aim_transaction_id=res.transaction_id,
                                         aim_response=res._as_dict,
                                         message=res.response_reason_text)
        billing_history.save()
        return success, billing_history

    def get_transaction_details(self):
        if self.aim_transaction_id == 0:
            return []
        from project.staff.models import AimTransaction
        return AimTransaction.objects.filter(transaction_id=self.aim_transaction_id).order_by('id')

    @property
    def debit_no_dot(self):
        return ("%.2f" % self.debit).replace(".", "")


class Refund(models.Model):
    payment = models.OneToOneField(BillingHistory, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    comment = models.CharField(max_length=512, null=True, blank=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    aim_transaction_id = models.CharField(max_length=50, null=True)


class FavoriteGenre(models.Model):
    user = models.ForeignKey(User)
    genre = models.ForeignKey('catalog.Genre')
    rating = models.IntegerField(default=0)

    @staticmethod
    def rate(user, genre, rating):
        if rating:
            r, _c = FavoriteGenre.objects.get_or_create(user=user, genre=genre)
            r.rating = rating
            r.save()
        else:
            FavoriteGenre.objects.filter(user=user, genre=genre).delete()

class CashOutPaymentMethod:
    MailCheck = 0
    Paypal = 1

CASH_OUT_PAYMENT_METHODS = (
    (CashOutPaymentMethod.MailCheck, 'Check'),
    (CashOutPaymentMethod.Paypal, 'Paypal'),
)

class CashOutOrderStatus:
    Submitted = 0
    Processed = 1

CASH_OUT_ORDER_STATUSES = (
    (CashOutOrderStatus.Submitted, 'Submitted'),
    (CashOutOrderStatus.Processed, 'Processed'),
)

STORE_CREDIT_RATE = 0.75

class CashOutOrder(models.Model):
    user = models.ForeignKey(User)

    status = models.IntegerField(choices=CASH_OUT_ORDER_STATUSES)
    payment_method = models.IntegerField(choices=CASH_OUT_PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))

    submit_date = models.DateTimeField(auto_now=True, editable=False)
    process_date = models.DateTimeField(null=True, editable=False)

    address1 = models.CharField(max_length=255, null=True, verbose_name='Address 1')
    address2 = models.CharField(max_length=255, null=True, verbose_name='Address 2', blank=True)
    city = models.CharField(max_length=100, null=True, verbose_name='City')
    county = models.CharField(max_length=100, null=True, verbose_name='County')
    state = models.CharField(max_length=2, null=True, verbose_name='State')
    zip_code = models.CharField(max_length=10, null=True, verbose_name='Zip')
