import sys
import decimal
import itertools
import base64
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import re

from django.db import models, transaction
from django.db.models import signals
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.safestring import mark_safe
from django_snippets.thirdparty.models.json_field import JSONField
from django.core.files.base import ContentFile
from django.db.models.signals import pre_delete
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from django_snippets.utils.datetime import inc_months
from endiciapy import Endicia
from endiciapy.enums import ImageFormat, MailClass, MailpieceShape, LabelType, LabelSize, SortType

from project.members.models import BillingCard, BillingHistory, TransactionStatus, TransactionType
from project.utils.mailer import mail
from project.taxes.models import Tax
from project.utils import create_aim
from project.billing.utils import send_billing_charge_approved

logger = logging.getLogger(__name__)


def split_zip(zip):
    z = zip.split("-")
    z += ["0000"] * (2 - len(z))
    return z

X_RENTAL_PLANS = (
    (0, "Monthly 1 Game Plan"),
    (1, "Monthly 2 Game Plan"),
    (2, "Monthly 3 Game Plan"),
    (3, "3 Months 2 Game Plan"),
    (4, "6 Months 2 Game Plan"),
    (5, "Monthly 1 Game Plan"),
    (6, "Monthly 2 Game Plan"),
    (7, "Monthly 2 Game Plan Free Trial"),
)


class BaseRentalPlan(models.Model):
    class Meta:
        db_table = "rent_rentalplan"
        ordering = ["plan"]

    plan = models.IntegerField(choices=X_RENTAL_PLANS, primary_key=True)
    description = models.CharField(max_length=50)
    first_month = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                      verbose_name="First month payment", blank=True)
    thereafter_months = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                      verbose_name="Thereafter months payment", blank=True)
    months = models.IntegerField(null=True, verbose_name="Payments interval in months", blank=True)
    expire_in = models.IntegerField(null=True, default=None, verbose_name="Expire in (months)", blank=True)
    store_credits = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount of bonus",
                                        default="0.0", blank=True)
    games_allowed = models.IntegerField(default=2, verbose_name="Amount of games at time")

    slug = models.SlugField(null=True, blank=True)
    out_per_month = models.IntegerField(null=True, blank=True)
    next_plan = models.ForeignKey("self", null=True, blank=True)
    first_payment_type = models.CharField(max_length=50, default="AUTH_CAPTURE")
    features = JSONField(null=True, blank=True)

    PlanA = 0  # Monthly 1 Game Plan
    PlanB = 1  # Monthly 2 Game Plan
    PlanC = 2  # Monthly 3 Game Plan
    PlanD = 3  # 3 Months 2 Game Plan
    PlanE = 4  # 6 Months 2 Game Plan
    PlanF = 5  # Monthly 1 Game Plan
    PlanG = 6  # Monthly 2 Game Plan
    PlanH = 7  # Monthly 2 Game Plan Free Trial

    _plans = [PlanA, PlanB, PlanC, PlanD, PlanE, PlanF, PlanG, PlanH]

    _payment_matrix = {
        # Plan: (first_month, thereafter_months, months, expire_in,
        # store_credits, description, allowed_games_amount)
        PlanA: ("7.95",   "8.99",  1,    None, None,   "Monthly 1 Game Plan", 1),
        PlanB: ("11.95",  "19.99", 1,    None, None,   "Monthly 2 Game Plan", 2),
        PlanC: ("29.99",  "29.99", 1,    None, None,   "Monthly 3 Game Plan", 3),  # Deprecated
        19: ("27.95",  "27.95", 1,    None, None,   "Monthly 3 Game Plan", 3),
        PlanD: ("59.99",  None,    None, 4,    "10.0", "3 Months 2 Game Plan", 2),
        PlanE: ("119.99", None,    None, 7,    "15.0", "6 Months 2 Game Plan", 2),

        PlanF: ("6.95",   "13.95",  1,    None, None,   "Monthly 1 Game Plan", 1),
        PlanG: ("10.95",  "20.95", 1,    None, None,   "Monthly 2 Game Plan", 2),
        # Hack here, we are setting next payment 10d, expire to None
        # and scheduled_plan to PlanB
        PlanH: ("20.95",  None, "10d",  None, None,   "Monthly 2 Game Plan", 2),
    }


class RentalPlan(BaseRentalPlan):
    class Meta:
        proxy = True

    @staticmethod
    def __get(plan):
        if type(plan) is not int:
            raise TypeError("plan should be int")
        if plan in RentalPlan.__cache:
            return RentalPlan.__cache[plan]
        try:
            row = RentalPlan.objects.get(plan=plan)
            r = (row.first_month, row.thereafter_months, row.months, row.expire_in, row.store_credits,
                 row.description, row.games_allowed)
        except RentalPlan.DoesNotExist:
            r = RentalPlan._payment_matrix[plan]
        RentalPlan.__cache[plan] = r
        return r
    __cache = {}


    @staticmethod
    def clear_cache():
        RentalPlan.__cache = {}

    @staticmethod
    def get_start_payment_amount(plan):
        a = RentalPlan.__get(plan)[0]
        return a and Decimal(a)

    @staticmethod
    def get_next_payment(plan, plan_start_date, last_payment_date, force_future_date=False):
        p = RentalPlan.__get(plan)
        if not p[2]:
            return None
        while True:
            date, amount = inc_months(last_payment_date, p[2]), p[1]
            if not force_future_date or date > datetime.today().date():
                break
            last_payment_date = date
        return date, amount and Decimal(amount)

    @staticmethod
    def get_expire_in(plan):
        return RentalPlan.__get(plan)[3]

    @staticmethod
    def get_reccuring_period(plan):
        return RentalPlan.__get(plan)[2]

    @staticmethod
    def get_expiration_date(plan, plan_start_date, downgrade=False):
        e = RentalPlan.__get(plan)[3]
        if not e:
            return None
        if downgrade:
            e -= 1
        return inc_months(plan_start_date, e)

    @staticmethod
    def get_bonus(plan):
        bonus = RentalPlan.__get(plan)[4]
        return bonus and Decimal(bonus)

    @staticmethod
    def get_prices(plan):
        r = RentalPlan.__get(plan)
        return r[0], r[1]

    @staticmethod
    def get_price_display(plan):
        r = RentalPlan.__get(plan)
        if r[1]:
            return mark_safe('<strong>$%s</strong>/month' % r[1])
        return mark_safe('<strong>$%s</strong>' % r[0])


    @staticmethod
    def get_allowed_games_amount(plan):
        return RentalPlan.__get(plan)[6]

    @staticmethod
    def get_description(plan):
        return RentalPlan.__get(plan)[5]

    @staticmethod
    def get_displayer(plan):
        class LazyDisplayer:
            def __init__(self, plan):
                self.plan = plan

            def __str__(self):
                return RentalPlan._RentalPlan__get(self.plan)[5]
        return LazyDisplayer(plan)

    @staticmethod
    def get_details(plan):
        return {
            RentalPlan.PlanA: {
                'plan': plan,
                'title': '2 Per Month',
                'subtitle': 'Monthly',
                'price': RentalPlan.get_price_display(plan),
                'description': RentalPlan.get_description(plan),
            },
            RentalPlan.PlanB: {
                'plan': plan,
                'title': 'Unlimited',
                'subtitle': 'Monthly',
                'price': RentalPlan.get_price_display(plan),
                'description': RentalPlan.get_description(plan),
            },
            RentalPlan.PlanC: {
                'plan': plan,
                'title': 'Unlimited',
                'subtitle': 'Monthly',
                'price': RentalPlan.get_price_display(plan),
                'description': RentalPlan.get_description(plan),
            },
            RentalPlan.PlanD: {
                'plan': plan,
                'title': 'Unlimited',
                'subtitle': '3 Months',
                'price': RentalPlan.get_price_display(plan),
                'description': RentalPlan.get_description(plan),
            },
            RentalPlan.PlanE: {
                'plan': plan,
                'title': 'Unlimited',
                'subtitle': '6 Months',
                'price': RentalPlan.get_price_display(plan),
                'description': RentalPlan.get_description(plan),
            },
        }.get(plan)

    @staticmethod
    def get_details2(plan, request=None):
        result = {
            RentalPlan.PlanA: {
                'plan': plan,
                'title': 'Monthly',
                'subtitle': '1 Game Plan',
                'features': [],
                'features2': [
                    '2 Per Month',
                ],
                'amount_to_charge': RentalPlan.get_start_payment_amount(plan),
            },
            RentalPlan.PlanB: {
                'plan': plan,
                'title': 'Monthly',
                'subtitle': '2 Game Plan',
                'features': [
                    '30% Discount',
                ],
                'features2': [
                    '30% Discount',
                    '1st Month Only',
                    '$13.99 Total',
                ],
                'amount_to_charge': RentalPlan.get_start_payment_amount(plan),
            },
            RentalPlan.PlanC: {
                'plan': plan,
                'title': 'Monthly',
                'subtitle': '3 Game Plan',
                'features2': [
                    'Extra 7% Off Purchases',
                    'GamePerks Rewards',
                ],
                'amount_to_charge': RentalPlan.get_start_payment_amount(plan),
            },
            RentalPlan.PlanD: {
                'plan': plan,
                'title': '3 Months Prepaid',
                'subtitle': '2 Game Plan',
                'features': [
                    'Get 1 Month Free!',
                    '4 Months Total',
                    '$10.00 Store Credits',
                ],
                'features2': [
                    '1 Extra Month Free!',
                    '$10.00 Store Credit',
                    '4 Months Total',
                ],
                'amount_to_charge': RentalPlan.get_start_payment_amount(plan),
            },
            RentalPlan.PlanE: {
                'plan': plan,
                'title': '6 Months Prepaid',
                'subtitle': '2 Game Plan',
                'features': [
                    'Get 1 Month Free!',
                    '7 Months Total',
                    '$15.00 Store Credits',
                ],
                'features2': [
                    '1 Extra Month Free!',
                    '$15.00 Store Credit',
                    '7 Months Total',
                ],
                'amount_to_charge': RentalPlan.get_start_payment_amount(plan),
            },
        }
        plan_obj = result.get(plan)
        if plan_obj and request:
            current_plan = MemberRentalPlan.get_current_plan(request.user)
            if current_plan and plan <= current_plan.plan:
                if plan != 0:
                    plan_obj['features'] = []
                    plan_obj['features2'] = []
                if plan in [RentalPlan.PlanA, RentalPlan.PlanB, RentalPlan.PlanC]:
                    plan_obj['amount_to_charge'] = RentalPlan.get_next_payment(plan, datetime.now(), datetime.now())[1]
        return plan_obj

    @staticmethod
    def get_membership_terms(plan):
        if plan == RentalPlan.PlanA:
            return '1 GAME out at-a-time (Limited)'
        if plan in [RentalPlan.PlanB, RentalPlan.PlanD, RentalPlan.PlanE]:
            return '2 GAMES out at-a-time (Unlimited)'
        return '3 GAMES out-at-time (Unlimited)'

    def __str__(self):
        return self.description


RENTAL_PLANS = (
    (RentalPlan.PlanA, RentalPlan.get_displayer(RentalPlan.PlanA)),
    (RentalPlan.PlanB, RentalPlan.get_displayer(RentalPlan.PlanB)),
    (RentalPlan.PlanC, RentalPlan.get_displayer(RentalPlan.PlanC)),
    (RentalPlan.PlanD, RentalPlan.get_displayer(RentalPlan.PlanD)),
    (RentalPlan.PlanE, RentalPlan.get_displayer(RentalPlan.PlanE)),
)


class RentalPlanStatus:
    Pending = 0
    Active = 1
    Delinquent = 2
    AutoCanceled = 3
    Collection = 4
    Canceled = 7
    CanceledP = 8
    TemporarySuspended = 9
    PersonalGame = 10
    Suspended = 11
    OnHold = 12
    Expired = 13
    FreeTrial = 14

RENTAL_PLAN_STATUS = (
    (0, "Pending"),
    (1, "Active"),
    (2, "Delinquent"),
    (3, "Auto Canceled"),
    (4, "Collection"),
    (7, "Canceled"),
    (8, "CanceledP"),
    (9, "Temporary Suspended"),
    (10, "Personal Game"),
    (11, "Suspended"),
    (12, "On Hold"),
    (13, "Expired"),
)

PAYMENT_TYPES = (
    ("AUTH_ONLY",) * 2,
    ("AUTH_CAPTURE",) * 2,
    ("PRIOR_AUTH_CAPTURE",) * 2,
)


class MemberRentalPlanException(Exception):
    pass


class BaseMemberRentalPlan(models.Model):
    class Meta:
        db_table = "rent_memberrentalplan"
        ordering = ['-created', ]

    user = models.ForeignKey(User, editable=False, null=True) # null=True is required --pashka
    plan = models.IntegerField(choices=RENTAL_PLANS, editable=False)
    status = models.IntegerField(choices=RENTAL_PLAN_STATUS, default=0, db_index=True)
    status_message = models.CharField(max_length=1024, default='', blank=True)
    created = models.DateTimeField(default=datetime.now, editable=False)
    start_date = models.DateField(default=datetime.now, db_index=True)
    expiration_date = models.DateField(null=True, editable=False)
    next_payment_date = models.DateField(null=True, db_index=True, blank=True)
    next_payment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    next_payment_type = models.CharField(max_length=255, null=True, blank=True, choices=PAYMENT_TYPES)

    payment_fails_count = models.IntegerField(default=0)
    delinquent_next_check = models.DateField(null=True, db_index=True, blank=True)
    delinquent_amout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    delinquent_tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    cancel_confirmation_code = models.CharField(max_length=50, db_index=True, null=True, editable=False)
    cancel_confirmation_timestamp = models.DateTimeField(db_index=True, null=True, editable=False)
    cancellation_date = models.DateField(db_index=True, null=True, editable=False)

    first_payment = models.ForeignKey(BillingHistory, null=True, editable=False)
    card_expired = models.BooleanField(default=False)

    hold_start_timestamp = models.DateTimeField(null=True, editable=False)
    hold_reactivate_timestamp = models.DateTimeField(db_index=True, null=True, editable=False)

    suspend_date = models.DateTimeField(null=True, blank=True)
    restored_from_history = models.BooleanField(default=False)

    scheduled_plan = models.SmallIntegerField(null=True, blank=True)
    downgraded_plan = models.BooleanField(default=False)


class MemberRentalPlan(BaseMemberRentalPlan):
    class Meta:
        proxy = True

    def __unicode__(self):
        if self.user:
            return 'User: %s, Plan: %s (%s)' % (self.user.get_profile().get_name_display(), self.get_plan_display(),
                                                self.get_status_display())
        else:
            return 'Plan: %s (%s)' % (self.get_plan_display(), self.get_status_display())

    @staticmethod
    def get_current_plan(user, exclude_canceled=True):
        if user.is_anonymous():
            return None
        for o in MemberRentalPlan.objects.filter(user=user).order_by('-created'):
            if o.status not in [RentalPlanStatus.Canceled, RentalPlanStatus.AutoCanceled]:
                return o
            if not exclude_canceled:
                return o
            return None
        return None


    @staticmethod
    @transaction.commit_on_success
    def create(user, plan, downgrade=False, send_email=True):
        plan = int(plan)
        plan_start_date = datetime.now()
        new_plan = MemberRentalPlan(user=user,
                                    plan=plan,
                                    status=RentalPlanStatus.Pending,
                                    start_date=plan_start_date,
                                    expiration_date=RentalPlan.get_expiration_date(plan, plan_start_date, downgrade))

        if user is not None:
            new_plan.activate(plan, send_email)
        new_plan.save()
        return new_plan

    @staticmethod
    def cancel_expired_plans():
        today = datetime.now().date
        qs = MemberRentalPlan.objects.filter(status__in=[RentalPlanStatus.Active, RentalPlanStatus.Pending])
        qs = qs.exclude(expiration_date=None).filter(expiration_date__lt=today)
        if settings.DEBUG:
            qs = qs.filter(user__id=1)
        for p in qs:
            if p.scheduled_plan is not None:
                p.activate_scheduled_plan()
            else:
                p.set_status(RentalPlanStatus.CanceledP)

    def activate_scheduled_plan(self):
        if self.scheduled_plan is None:
            return
        new_plan = self.scheduled_plan
        user = self.user
        self.delete()
        new_p = MemberRentalPlan.create(user, new_plan, True, send_email=False)
        new_p.status = RentalPlanStatus.Active
        new_p.downgraded_plan = True
        new_p.next_payment_date = datetime.now()
        next_payment = RentalPlan.get_next_payment(new_plan, datetime.now(), datetime.now())
        if next_payment:
            next_payment = next_payment[1]
        else:
            next_payment = RentalPlan.get_start_payment_amount(new_plan)
        new_p.next_payment_amount = next_payment
        new_p.save()

        orders = RentOrder.objects.filter(user=new_p.user, status__in=[RentOrderStatus.Pending, RentOrderStatus.Prepared])
        if orders.count():
            new_p.is_valid()
            for o in orders:
                o.date_rent = datetime.now()
                o.save()

        return new_p


    @staticmethod
    def cancel_dead_plans():
        date_x = datetime.now() - timedelta(29)
        aim = create_aim()
        qs = MemberRentalPlan.objects.filter(status=RentalPlanStatus.Pending)
        qs = qs.filter(created__lte=date_x)
        for plan in qs:
            fp = plan.first_payment
            if fp:
                logger.debug('Canceling plan %s...', plan)
                aim_data = {}
                if plan.user:
                    aim_data['x_email'] = plan.user.email
                    aim_data['x_cust_id'] = plan.user.id
                aim.void(fp.aim_transaction_id, aim_data)
                fp.status = TransactionStatus.Canceled
                fp.save()
            plan.set_status(RentalPlanStatus.AutoCanceled)


    def get_last_payment(self):
        lp = BillingHistory.objects.filter(user=self.user,
                                           type=TransactionType.RentPayment,
                                           status__in=[TransactionStatus.Authorized, TransactionStatus.Passed]).order_by('-timestamp')
        for x in lp:
            return x
        return None


    def rentals_remaining(self):
        from project.inventory.models import InventoryStatus

        if self.plan == RentalPlan.PlanA:
            lp = BillingHistory.objects.filter(user=self.user,
                                               type=TransactionType.RentPayment,
                                               status__in=[TransactionStatus.Authorized, TransactionStatus.Passed]).order_by('-timestamp')
            if not lp:
                return 0
            lp = lp[0]
            print lp.timestamp
            x = 2 - RentOrder.objects.filter(user=self.user, date_rent__gte=lp.timestamp).exclude(status=RentOrderStatus.Pending).exclude(inventory__status__in=[InventoryStatus.USPSLost, InventoryStatus.Lost]).count()
            return x if x > 0 else 0
        return -1


    def refund_first_payment(self):
        if not self.first_payment:
            return
        if self.first_payment.get_refund() or self.first_payment.status == TransactionStatus.Canceled:
            return
        if self.first_payment.is_setted():
            self.first_payment.refund_transaction(comment='Made Refund of Signup Authorization')
        else:
            self.first_payment.void_transaction()


    def finish_cancellation(self):
        orders = RentOrder.objects.filter(user=self.user, date_rent__gte=self.created).exclude(status=RentOrderStatus.Canceled)
        logger.debug('First payment: %s', self.first_payment)
        logger.debug('Orders: %s', orders)
        if self.first_payment and orders.count() == 0:
            logger.debug('First payment could be refunded')
            self.refund_first_payment()
        self.status = RentalPlanStatus.Canceled
        self.save()
        self.send_cancellation_notification()
        self.delete()


    def get_payment_description(self, new_or_reccuring, trans_id, reccuring=False):
        if reccuring:
            invoice_num = 'RENT_SUBS_%s_%s' % (self.user.id, trans_id)
        elif new_or_reccuring:
            invoice_num = 'RENT_NEW_%s' % trans_id
        else:
            if MemberRentalPlanHistory.objects.filter(user=self.user, plan=self.plan).count() == 0:
                invoice_num = 'RENT_CHNG_%s_%s' % (self.user.id, trans_id)
            else:
                invoice_num = 'RENT_REAC_%s_%s' % (self.user.id, trans_id)

        def format_date(d):
            from django.template.defaultfilters import date
            return date(d, 'M j, Y') if d else '--'

        today = datetime.now().date()

        np = RentalPlan.get_next_payment(self.plan, self.start_date or today, self.next_payment_date or today)
        if new_or_reccuring:
            if np:
                d = 'Monthly Membership'
                d2 = np[0]
            else:
                d = 'Prepaid Membership'
                d2 = RentalPlan.get_expiration_date(self.plan, today)
        else:
            d = 'Change Plan'
            if np:
                d2 = np[0]
            else:
                d2 = RentalPlan.get_expiration_date(self.plan, today)

        if not reccuring:
            #description for new plan payment is different than recurring plan payment ticket 76
            description = ' - '.join([d, format_date(self.start_date or today), format_date(self.next_payment_date)])
        else:
            description = ' - '.join([d, format_date(self.next_payment_date or self.start_date or today), format_date(d2)])

        return invoice_num, description

    def _create_aim_data(self, aim_data, card, shipping_data, billing_data, invoice_num,
                         description, user, profile=None):
        aim_data.update({
            'number': card['number'],
            'exp': '/'.join(('%s' % card['exp_month'], ('%s' % card['exp_year'])[-2:])),
            'code': card['code'],
            'shipping': shipping_data or (profile or self.user.get_profile()).get_shipping_data(),
            'billing': billing_data or (profile or self.user.get_profile()).get_billing_data(),
            'invoice_num': invoice_num,
            'description': description,
        })
        if user:
            if 'x_email' not in aim_data: aim_data['x_email'] = user.email
            if 'x_cust_id' not in aim_data: aim_data['x_cust_id'] = user.id
        return aim_data

    def authorize_money(self, amount, tax, invoice_num, description, card=None,
                   shipping_data=None, billing_data=None, aim=None, aim_data={}):
        logger.debug('Authorizing amount of $%s (+$%s tax)...', amount, tax)
        if not card:
            billing_card = BillingCard.get(self.user)
            if not billing_card or not billing_card.data or not billing_card.data['number']:
                self.delinquent_amout = amount
                self.delinquent_tax = tax
                self.set_status(RentalPlanStatus.Delinquent, 'You need to setup your billing information.')
                return False, None
            card = billing_card.data
            card['display_number'] = billing_card.display_number
        aim = create_aim()
        aim_data = self._create_aim_data(aim_data, card, shipping_data, billing_data, invoice_num, description, self.user)
        res = aim.authorize(amount + tax, **aim_data)
        logger.debug('AIM response code: %s (%s)', res.response_code, res.response_reason_code)
        if res.response_code == 2:
            if res.response_reason_code in [2, 3, 4]:
                msg = 'Insufficient funds are available for this transaction.'
            elif res.avs_response == 'U':
                msg = 'We do not accept prepaid cards.'
            else:
                msg = 'We are unable to process you credit card at this time.'
            self.delinquent_amout = amount
            self.delinquent_tax = tax
            self.set_status(RentalPlanStatus.Delinquent, msg)
            return False, res
        elif res.response_code != 1:
            msg = 'Insufficient funds are available.'
            self.delinquent_amout = amount
            self.delinquent_tax = tax
            self.set_status(RentalPlanStatus.Delinquent, msg)
            return False, res
        return True, res

    def take_money(self, amount, tax, invoice_num, description, card=None,
                   shipping_data=None, billing_data=None, aim=None,
                   aim_data={}, profile=None, aim_method="capture"):
        applied_credits = 0
        if not self.card_expired:
            logger.debug('Taking amount of $%s (+$%s tax)...', amount, tax)
            if not card:
                if profile:
                    billing_card = profile.get_payment_card()
                else:
                    billing_card = BillingCard.get(self.user)
                if not billing_card or not billing_card.data or not billing_card.data['number']:
                    self.delinquent_amout = amount
                    self.delinquent_tax = tax
                    self.set_status(RentalPlanStatus.Delinquent, 'You need to setup your billing information.')
                    return False, None, applied_credits, None
                card = billing_card.data
                card['display_number'] = billing_card.display_number

            aim = create_aim()
            aim_data = self._create_aim_data(aim_data, card, shipping_data, billing_data, invoice_num,
                                             description, self.user, profile=profile)

            try:
                profile = profile or self.user.get_profile()
            except:
                pass

            if profile:
                credits_amount = profile.store_credits
            else:
                credits_amount = 0

            if credits_amount > 0:
                if credits_amount >= amount:
                    applied_credits = amount
                    amount = 0
                    profile.withdraw_store_credits(applied_credits, force=True)
                    return True, None, applied_credits, 0
                else:
                    applied_credits = credits_amount
                    amount -= credits_amount

            applied_amount = amount
            res = getattr(aim, aim_method)(amount + tax, **aim_data)

            logger.debug('AIM response code: %s (%s)', res.response_code, res.response_reason_code)

            if res.response_code == 1:
                if profile:
                    profile.withdraw_store_credits(applied_credits, force=True)
                return True, res, applied_credits, applied_amount

            self.delinquent_amout = amount
            self.delinquent_tax = tax

            if res.response_code == 3 and res.response_reason_code in [6, 7, 8]:
                self.card_expired = True
                msg = 'Credit card is expired'
            elif res.response_reason_code in [2, 3, 4]:
                msg = 'Insufficient funds are available for this transaction.'
            elif res.avs_response == 'U':
                msg = 'We do not accept prepaid cards.'
            else:
                msg = 'We are unable to process you credit card at this time.'
        else:
            msg = 'Credit card is expired'
            res = None
            logger.debug(msg)

        if self.status != RentalPlanStatus.Collection:
            self.set_status(RentalPlanStatus.Delinquent, msg)
        return False, res, applied_credits, amount

    def is_valid(self):
        logger.debug('Check plan if it valid...')
        if self.status == RentalPlanStatus.Active:
            logger.debug('  YES')
            return True
        if self.status != RentalPlanStatus.Pending:
            logger.debug('  NO')
            return False
        if not self.first_payment:
            logger.debug('  NO - No first payment')
            return False
        if self.first_payment.setted:
            logger.debug('  YES - First payment is already setted')
            return True

        logger.debug('  Trying to capture first payment...')

        aim = create_aim()
        profile = self.user.get_profile()

        fp = self.first_payment
        billing = profile.get_billing_data()
        shipping = profile.get_shipping_data()
        aim_data = {
            'x_email': self.user.email,
            'x_cust_id': self.user.id,
            'x_tax': fp.tax,
        }

        billing_history = BillingHistory.create(user=fp.user,
                                                payment_method=fp.payment_method,
                                                description=fp.description,
                                                debit=fp.debit,
                                                reason=fp.reason,
                                                type=fp.type)
        billing_history.card_data = profile.get_billing_card_data()
        billing_history.tax = fp.tax
        billing_history.refered_transaction = fp

        res = aim.prior_auth_capture(fp.get_debit_total(), fp.aim_transaction_id, billing, shipping, **aim_data)
        billing_history.aim_transaction_id = res.transaction_id
        billing_history.aim_response = res._as_dict
        billing_history.message = res.response_reason_text
        if res.response_code == 1:
            billing_history.status = TransactionStatus.Passed
            billing_history.save()
            self.first_payment = billing_history
            self.status = RentalPlanStatus.Active
            self.save()
            logger.debug('  SUCCESSFUL')
            return True
        logger.debug('  DECLINED')
        billing_history.status = TransactionStatus.Declined
        billing_history.save()
        if res.response_code == 3 and res.response_subcode in [6, 7, 8]:
            self.set_status(RentalPlanStatus.AutoCanceled, 'Expired card')
        else:
            self.delinquent_amout = fp.debit - fp.tax
            self.delinquent_tax = fp.tax
            self.set_status(RentalPlanStatus.Delinquent, 'Insufficient funds are available.')
        self.send_problem_with_transaction_email()
        return False

    #malcala
    def capture_1b(self):
        '''Helper to capture first auth payment for issue 1b
        '''

        logger.debug('  Trying to capture first payment...')

        aim = create_aim()
        profile = self.user.get_profile()

        fp = self.first_payment
        billing = profile.get_billing_data()
        shipping = profile.get_shipping_data()
        aim_data = {
            'x_email': self.user.email,
            'x_cust_id': self.user.id,
            'x_tax': fp.tax,
        }

        billing_history = BillingHistory.create(user=fp.user,
                                                payment_method=fp.payment_method,
                                                description=fp.description,
                                                debit=fp.debit,
                                                reason=fp.reason,
                                                type=fp.type)
        billing_history.card_data = profile.get_billing_card_data()
        billing_history.tax = fp.tax
        billing_history.refered_transaction = fp

        res = aim.prior_auth_capture(fp.get_debit_total(), fp.aim_transaction_id, billing, shipping, **aim_data)
        billing_history.aim_transaction_id = res.transaction_id
        billing_history.aim_response = res._as_dict
        billing_history.message = res.response_reason_text
        if res.response_code == 1:
            billing_history.status = TransactionStatus.Passed
            billing_history.save()
            self.first_payment = billing_history
            self.status = RentalPlanStatus.Active
            self.save()
            logger.debug('  SUCCESSFUL')
            return True
        logger.debug('  DECLINED')
        billing_history.status = TransactionStatus.Declined
        billing_history.save()
        if res.response_code == 3 and res.response_subcode in [6, 7, 8]:
            self.set_status(RentalPlanStatus.AutoCanceled, 'Expired card')
        else:
            self.delinquent_amout = fp.debit - fp.tax
            self.delinquent_tax = fp.tax
            self.set_status(RentalPlanStatus.Delinquent, 'Insufficient funds are available.')
        self.send_problem_with_transaction_email()
        return False

    @transaction.commit_on_success
    def buy_games_at_home(self, description='Plan Cancellation', penalty_reason=('CANC', 'Rent Cancellation')):
        return RentOrder.buy_games_at_home(self.user, description, penalty_reason)

    def activate(self, new, send_email=True):
        if self.status != RentalPlanStatus.Pending:
            return

        prev_plan = None
        for p in MemberRentalPlan.objects.filter(user=self.user).exclude(id=self.id).order_by('-id'):
            prev_plan = p.plan
            break
        MemberRentalPlan.objects.filter(user=self.user).exclude(id=self.id).delete()

        next_payment = RentalPlan.get_next_payment(self.plan, self.start_date, self.start_date)
        if next_payment:
            self.next_payment_date, self.next_payment_amount = next_payment

        self.set_status(RentalPlanStatus.Active)
        self.save()

        if self.plan > prev_plan and prev_plan:
            profile = self.user.get_profile()
            profile.add_bonus_store_credits(RentalPlan.get_bonus(self.plan))

        if send_email:
            self.send_plan_subscription_successfull_email()


    def take_recurring_billing(self, aim_method="capture"):
        user = self.user
        if not user:
            return
        profile = user.get_profile()

        amount = self.next_payment_amount
        if not amount:
            return

        logger.debug('Try to take %s charge from %s...', self.next_payment_amount, self.user)

        billing_address = profile.get_billing_address_data()

        tax = Tax.get_value(billing_address['state'], billing_address['county'])
        tax_amount = decimal.Decimal('%.2f' % (amount * tax / decimal.Decimal('100.0')))

        billing_history = BillingHistory.create(self.user, profile.get_billing_card_display(),
            debit=amount, reason='rent', type=TransactionType.RentPayment)
        billing_history.card_data = profile.get_billing_card_data()
        billing_history.tax = tax_amount

        invoice_num, description = self.get_payment_description(True, billing_history.id, True)

        billing_history.description = description

        res, aim_response, applied_credits, applied_amount = self.take_money(
            amount, tax_amount, invoice_num, description, aim_data={},
            aim_method=aim_method)

        billing_history.applied_credits = applied_credits
        billing_history.debit = applied_amount
        if applied_amount == 0:
            billing_history.payment_method = "Store Credits"

        if aim_response:
            billing_history.aim_transaction_id = aim_response.transaction_id
            billing_history.aim_response  = aim_response._as_dict
            billing_history.message = aim_response.response_reason_text

        if not res:
            billing_history.status = TransactionStatus.Declined
            billing_history.save()
            self.send_recurring_billing_charge_declined(1)
            return False

        billing_history.save()
        billing_card = BillingCard.get(self.user)

        if applied_amount > 0:
            self.send_billing_charge_approved(billing_card.get_type_display(), billing_card.display_number, applied_amount)

        next_payment = RentalPlan.get_next_payment(self.plan, self.start_date, self.next_payment_date, force_future_date=True)
        logger.debug('Next payment: %s', next_payment)
        if next_payment:
            self.next_payment_date, self.next_payment_amount = next_payment
        else:
            self.next_payment_date = None
            self.next_payment_amount = None
        profile.clear_locked_store_credits()
        self.set_status(RentalPlanStatus.Active)
        return True

#    @transaction.commit_on_success
    def take_delinquent_payment(self, card_changed=False, profile=None, aim_data={}):
        logger.debug('Try to take charge from %s...', self.user)

        amount = self.delinquent_amout or self.next_payment_amount
        if not amount:
            return False, None
        tax = self.delinquent_tax or decimal.Decimal('0.0')

        user = self.user
        if not user:
            return False, None

        profile = profile or user.get_profile()

        aim_response = None

        if not self.card_expired or card_changed:
            self.card_expired = False

            billing_history = BillingHistory.create(self.user, profile.get_billing_card_display(),
                debit=amount, reason='rent', type=TransactionType.RentPayment)
            billing_history.card_data = profile.get_billing_card_data()
            billing_history.tax = tax

            invoice_num, description = self.get_payment_description(True, billing_history.id, True)

            billing_history.description = description
            res, aim_response, applied_credits, applied_amount = self.take_money(amount, tax, invoice_num, description,
                                                                 profile=profile, aim_data=aim_data)
            billing_history.applied_credits = applied_credits
            if aim_response:
                billing_history.aim_transaction_id = aim_response.transaction_id
                billing_history.aim_response  = aim_response._as_dict
                billing_history.message = aim_response.response_reason_text
            if res:
                billing_history.save()

                next_payment = RentalPlan.get_next_payment(self.plan,
                                                           self.next_payment_date,
                                                           self.next_payment_date,
                                                           force_future_date=True)
                logger.debug('Next payment: %s', next_payment)
                if next_payment:
                    self.next_payment_date, self.next_payment_amount = next_payment
                profile.clear_locked_store_credits()
                self.set_status(RentalPlanStatus.Active)

                billing_card = BillingCard.get(self.user)
                self.send_billing_charge_approved(billing_card.get_type_display(), billing_card.display_number, amount + tax)
                return True, aim_response
            billing_history.status = TransactionStatus.Declined
            billing_history.save()

        if not card_changed:
            self.payment_fails_count += 1
            if self.payment_fails_count > 4:
                self.delinquent_next_check = None
                for order in RentOrder.objects.filter(user=self.user, status=RentOrderStatus.Pending):
                    order.status = RentOrderStatus.Canceled
                    order.save()

                unreturned_games = RentOrder.objects.filter(user=self.user, status__in=[RentOrderStatus.Prepared, RentOrderStatus.Shipped])
                unreturned_games_count = unreturned_games.count()
                if unreturned_games_count > 0:
                    profile = self.user.get_profile()
                    if profile.unlocked_store_credits >= amount + tax:
                        profile.withdraw_store_credits(amount + tax, save=True)

                        BillingHistory.log(self.user, 'Store Credits', description,
                                           debit=amount, status=TransactionStatus.Passed,
                                           type=TransactionType.RentPayment)
                        next_payment = RentalPlan.get_next_payment(self.plan,
                                                                   self.start_date,
                                                                   self.next_payment_date,
                                                                   force_future_date=True)
                        if next_payment:
                            self.next_payment_date, self.next_payment_amount = next_payment
                        self.set_status(RentalPlanStatus.Active)
                    else:
                        self.set_status(RentalPlanStatus.Collection)
                else:
                    self.set_status(RentalPlanStatus.AutoCanceled)
            else:
                attempt = {2: 2, 3: 3, 4: 4, }.get(self.payment_fails_count)
                if attempt:
                    self.send_recurring_billing_charge_declined(attempt)
                self.delinquent_next_check = datetime.now().date() + timedelta(5)
        self.save()
        return False, aim_response

    @staticmethod
    def purge_expired_plans():
        today = datetime.now().date()
        for p in MemberRentalPlan.objects.filter(expiration_date__lt=today, status=RentalPlanStatus.Active):
            p.status = RentalPlanStatus.Expired
            p.save()

    @staticmethod
    def cleanup_expired_cancellations():
        date_x = datetime.now() - timedelta(2)
        plans = MemberRentalPlan.objects.all()
        plans = plans.filter(status__in=[RentalPlanStatus.Active, RentalPlanStatus.Delinquent, RentalPlanStatus.Pending])
        plans = plans.filter(cancel_confirmation_timestamp__lt=date_x)
        for p in plans:
            p.cancel_confirmation_code = None
            p.cancel_confirmation_timestamp = None
            p.save()
        CancellationReason.objects.filter(is_confirmed=False, confirmation_date__lt=date_x).delete()

    def set_status(self, status, message='', save=True):
        logger.debug('Change status to: %s %s', status, message)
        self.status = status
        self.status_message = message
        if status == RentalPlanStatus.Delinquent:
            if not self.delinquent_next_check:
                self.payment_fails_count = 1
                self.delinquent_next_check = datetime.now().date() + timedelta(5)
        elif status == RentalPlanStatus.AutoCanceled:
            self.save()
            self.send_autocancel_email()
            self.delete()
            return
        else:
            self.payment_fails_count = 0
            self.delinquent_next_check = None
            self.delinquent_amout = None
            self.card_expired = False
        if save:
            self.save()

    def get_pending_items(self):
        free_cells = self.remaining_rents
        return RentList.get(self.user, available=True)[:free_cells] if free_cells > 0 else []

    def get_games_at_time(self):
        return RentalPlan.get_allowed_games_amount(self.plan)
    games_at_time = property(get_games_at_time)

    def get_expire_in(self):
        if not self.expiration_date:
            return None
        m1 = self.start_date.month
        m2 = self.expiration_date.month
        if m1 > m2: m2 += 12
        return m2 - m1
    expire_in = property(get_expire_in)

    def get_remaining_rents(self):
        if self.status not in [RentalPlanStatus.Pending, RentalPlanStatus.Active]:
            return 0
        allowed_games = RentalPlan.get_allowed_games_amount(self.plan)
        current_order_amount = RentOrder.objects.filter(user=self.user,
                                                        status__in=[RentOrderStatus.Shipped,
                                                                    RentOrderStatus.Pending,
                                                                    RentOrderStatus.Prepared]).count()
        r = allowed_games - current_order_amount
        return r if r > 0 else 0
    remaining_rents = property(get_remaining_rents)

    def get_period_in_months(self):
        return {
            RentalPlan.PlanA: 1,
            RentalPlan.PlanB: 1,
            RentalPlan.PlanC: 1,
            RentalPlan.PlanD: 4,
            RentalPlan.PlanE: 7,
        }.get(self.plan, 1)

    def get_start_payment_amount(self):
        return RentalPlan.get_start_payment_amount(self.plan)

    def get_next_period_date(self):
        logger.debug('Next period date: %s', self.next_payment_date)
        if not self.next_payment_date:
            return None
        return self.next_payment_date + timedelta(1)
    next_period_date = property(get_next_period_date)

    def is_active(self):
        return self.status in [RentalPlanStatus.Pending, RentalPlanStatus.Active]

    def is_holdable(self):
        return self.status in [RentalPlanStatus.OnHold, RentalPlanStatus.Active]

    def is_new(self):
        return self.status == RentalPlanStatus.Pending

    def get_plan_details(self):
        return RentalPlan.get_details(self.plan)

    def get_membership_terms(self):
        return RentalPlan.get_membership_terms(self.plan)

    def suspend_plan(self,message=''):
        message = message or '''The account was closed due to "Terms of Use" violations.
               1.    Account Problems: Returned Mail or Personal Game Received.
               2.    Terms of Use Violations: Excessive Claims (3 Strikes), Fraud or Duplicate Account.
'''
        self.suspend_date = datetime.now()
        self.status = RentalPlanStatus.Suspended
        self.status_message = message
        self.save()
        self.send_rent_account_suspension_email()

    def send_problem_with_transaction_email(self):
        # TODO: IMPLEMENT ME!!!
        pass

    def send_rent_account_suspension_email(self):
        mail(self.user.email, 'emails/rent_emails/account_suspension_email.html', {
            'plan': self,
            'user': self.user,
        }, subject='Gamemine - Rent Account Suspension')

    def send_autocancel_email(self):
        if not self.user:
            return
        mail(self.user.email, 'emails/rent_emails/autocancel_email.html', {
            'plan': self,
            'user': self.user,
        }, subject='Gamemine - Rent Account Membership Canceled')

    def send_plan_subscription_successfull_email(self):
        from project.catalog.models import Item
        mail(self.user.email, 'emails/rent_emails/plan_subscription_successfull.html', {
            'user': self.user,
            'plan': self,
            'new_releases': Item.list_new_releases(6),
            'coming_soon': Item.list_all()[:6],
        }, subject='Gamemine - Thanks for Joining Gamemine!')

    def send_recurring_billing_charge_declined(self, attempt):
        subjects = {
            1: 'Oops, we have a billing problem!',
            2: 'Problem with your Recent Transaction!',
            3: 'We Can\'t Send you Games!',
            4: 'Problem with your Recent Transaction!',
            5: 'Your Rent Account is about to be Cancelled!',
            6: 'Gamemine account has been canceled - Please return games',
            }
        credit_card = self.user.get_profile().get_payment_card()

        display_number = credit_card.display_number
        if not display_number and credit_card.data:
            display_number = credit_card.data.number
        display_number = (display_number or '')[-4:]

        mail(self.user.email, 'emails/rent_emails/recurring_billing_charge_declined.html', {
            'plan': self,
            'attempt': attempt,
            'user': self.user,
            'credit_card_type': credit_card.get_type_display(),
            'credit_card_number': display_number,
            'unreturned_orders': RentOrder.objects.filter(user=self.user, status=RentOrderStatus.Shipped),
            'due_date': datetime.now().date() + timedelta(7),
        }, subject=subjects.get(attempt, 'Oops, we have a billing problem!'))

    def send_cancel_request(self, reason):
        from uuid import uuid4
        self.cancel_confirmation_code = str(uuid4())
        self.cancel_confirmation_timestamp = datetime.now()
        self.save()

        reason.confirmation_code = self.cancel_confirmation_code
        reason.confirmation_date = self.cancel_confirmation_timestamp
        reason.save()

        url = 'http://%s%s' % (
            Site.objects.get_current().domain,
            reverse('members:cancel_membership_confirm', args=[self.cancel_confirmation_code]))

        mail(self.user.email, 'emails/rent_emails/cancel_request.html', {
            'plan': self,
            'nickname': self.user.username,
            'url': url,
            'user': self.user,
        }, subject='Gamemine - Confirm Your Subscription Cancellation!')

    def send_cancellation_notification(self):
        mail(self.user.email, 'emails/rent_emails/cancellation_notification.html', {
            'plan': self,
            'user': self.user,
        }, subject='Gamemine - Rent Account Membership Canceled')

    def send_billing_charge_approved(self, cc_type, cc_num, amount):
        send_billing_charge_approved(self.user, amount)

    def send_personal_game_received(self):
        mail(self.user.email, 'emails/rent_emails/personal_game_received.html', {
            'user': self.user,
            'orders': RentOrder.objects.filter(status=RentOrderStatus.Shipped, user=self.user),
        }, subject='Account Restricted - Personal Game Received')

    def send_account_is_held(self):
        mail(self.user.email, 'emails/rent_emails/account_is_held.html', {
            'user': self.user,
            'plan': self,
            'due_date': datetime.now() + timedelta(10),
            'orders': RentOrder.objects.filter(status__in=[RentOrderStatus.Prepared, RentOrderStatus.Shipped], user=self.user),
        }, subject='Gamemine - Your Account is on Hold')

    def send_account_is_reactivated(self):
        mail(self.user.email, 'emails/rent_emails/account_is_reactivated.html', {
            'user': self.user,
            'plan': self,
        }, subject='Gamemine - Your Rent Account is Reactivated')

    @transaction.commit_on_success
    def put_on_hold(self, till_date):
        if self.status == RentalPlanStatus.OnHold:
            self.hold_reactivate_timestamp = till_date
            self.save()
            return True
        if self.status == RentalPlanStatus.Active:
            for order in RentOrder.objects.filter(user=self.user, status=RentOrderStatus.Pending):
                order.status = RentOrderStatus.Canceled
                order.save()

            self.status = RentalPlanStatus.OnHold
            self.hold_start_timestamp = datetime.now()
            self.hold_reactivate_timestamp = till_date
            self.save()
            self.send_account_is_held()

            return True
        return False

    @transaction.commit_on_success
    def reactivate(self):
        if self.status == RentalPlanStatus.OnHold:
            today = datetime.now().date()
            if self.expiration_date and self.expiration_date < today:
                self.expiration_date = today
            elif self.next_payment_date and self.next_payment_date < today:
                self.next_payment_date = today
            self.status = RentalPlanStatus.Active
            self.save()
            self.send_account_is_reactivated()

class MemberRentalPlanHistory(models.Model):
    user = models.ForeignKey(User)
    plan = models.IntegerField(choices=RENTAL_PLANS)
    status = models.IntegerField(choices=RENTAL_PLAN_STATUS, default=0)
    start_date = models.DateField()
    finish_date = models.DateField(default=datetime.now)

    @staticmethod
    def create(member_plan):
        if member_plan.user:
            MemberRentalPlanHistory(user=member_plan.user,
                                    plan=member_plan.plan,
                                    status=member_plan.status,
                                    start_date=member_plan.start_date).save()

    def get_active_days(self):
        return self.finish_date - self.start_date

    def get_billing_cycles(self):
        b = BillingHistory.objects.filter(user=self.user,
                                          timestamp__gte=self.start_date,
                                          timestamp__lt=self.finish_date,
                                          type=TransactionType.RentPayment,
                                          status=TransactionStatus.Passed)
        return b.count()

    def cancel_reason(self):
        rr = CancellationReason.objects.filter(user=self.user,
                                               creation_date__gte=self.start_date,
                                               creation_date__lt=self.finish_date)
        for r in rr:
            return r
        return None


    def get_cancel_reason(self):
        rr = CancellationReason.objects.filter(user=self.user,
                                               creation_date__gte=self.start_date,
                                               creation_date__lt=self.finish_date)
        for r in rr:
            reasons = []
            if r.shipping_to_slow: reasons.append('Shipping too slow')
            if r.too_many_shipping_problems: reasons.append('Too many shipping problems')
            if r.website_is_not_user_friendly: reasons.append('Website is not user friendly')
            if r.switching_to_another_service: reasons.append('Switching to another service')
            if r.not_enough_variety_of_games: reasons.append('Not enough variety of games')
            if r.moving_traveling: reasons.append('Moving / Traveling')
            if r.poor_customer_service: reasons.append('Poor customer service')
            if r.service_costs_too_much: reasons.append('Service costs too much')
            if r.only_signed_up_for_promotion: reasons.append('Only signed up for promotion')
            if r.poor_inventory_availability: reasons.append('Poor inventory availability')
            return '. '.join(reasons)
        return ''

    def get_games_out_amount(self):
        rr = RentOrder.objects.filter(user=self.user,
                                      date_rent__gte=self.start_date,
                                      date_rent__lt=self.finish_date).exclude(status__in=[
                                                RentOrderStatus.Canceled,
                                                RentOrderStatus.AutoCanceled,
                                                RentOrderStatus.AutoCanceledByAstral,
                                                RentOrderStatus.AutoCanceledByManualCheck])
        return rr.count()

    def get_games_in_amount(self):
        rr = RentOrder.objects.filter(user=self.user,
                                      date_rent__gte=self.start_date,
                                      date_rent__lt=self.finish_date,
                                      status=RentOrderStatus.Returned)
        return rr.count()


def member_reantal_plan_pre_delete(sender, instance, **kwargs):
    MemberRentalPlanHistory.create(instance)
pre_delete.connect(member_reantal_plan_pre_delete, MemberRentalPlan)


class CancellationReason(models.Model):
    user = models.ForeignKey(User, editable=False, null=True)
    plan = models.IntegerField(choices=RENTAL_PLANS, editable=False, null=True)
    creation_date = models.DateTimeField(default=datetime.now, db_index=True)
    is_confirmed = models.BooleanField(default=False, db_index=True)
    confirmation_code = models.CharField(max_length=50, null=True, db_index=True)
    confirmation_date = models.DateTimeField(null=True, db_index=True)

    shipping_to_slow = models.BooleanField(default=False)
    too_many_shipping_problems = models.BooleanField(default=False)
    website_is_not_user_friendly = models.BooleanField(default=False)
    switching_to_another_service = models.BooleanField(default=False)
    not_enough_variety_of_games = models.BooleanField(default=False)
    moving_traveling = models.BooleanField(default=False)
    poor_customer_service = models.BooleanField(default=False)
    service_costs_too_much = models.BooleanField(default=False)
    only_signed_up_for_promotion = models.BooleanField(default=False)
    poor_inventory_availability = models.BooleanField(default=False)
    notes = models.TextField()


class RentPlanCancellationReason(models.Model):
    user = models.ForeignKey(User)
    plan = models.IntegerField(choices=RENTAL_PLANS, db_index=True)
    timestamp = models.DateTimeField(default=datetime.now, db_index=True)

    shipping_to_slow = models.BooleanField(default=False, db_index=True)
    too_many_shipping_problems = models.BooleanField(default=False, db_index=True)
    website_is_not_user_friendly = models.BooleanField(default=False, db_index=True)
    switching_to_another_service = models.BooleanField(default=False, db_index=True)
    not_enough_variety_of_games = models.BooleanField(default=False, db_index=True)
    moving_traveling = models.BooleanField(default=False, db_index=True)
    poor_customer_service = models.BooleanField(default=False, db_index=True)
    service_costs_too_much = models.BooleanField(default=False, db_index=True)
    only_signed_up_for_promotion = models.BooleanField(default=False, db_index=True)
    poor_inventory_availability = models.BooleanField(default=False, db_index=True)

    notes = models.TextField(default='')


class RentOrderStatus:
    Pending = 0
    Shipped = 1
    Returned = 2
    Canceled = 3
    Prepared = 4
    Sale = 5
    AutoCanceled = 6 # Set during import
    AutoCanceledByAstral = 7
    AutoCanceledByManualCheck = 8
    Claim = 9

RENT_GAME_STATUSES = (
    (0, 'Pending'),
    (1, 'Shipped'),
    (2, 'Returned'),
    (3, 'Canceled'),
    (4, 'Prepared'),
    (5, 'Sale'),
    (6, 'Canceled'),
    (7, 'Canceled'),
    (8, 'Canceled'),
    (9, 'Claim'),
)


class RentOrder(models.Model):
    class Meta:
        verbose_name = 'Rent order'
        verbose_name_plural = 'Rent orders'
        ordering = ['-date_rent']

    user = models.ForeignKey(User, editable=False)
    item = models.ForeignKey('catalog.Item', editable=False)
    status = models.IntegerField(choices=RENT_GAME_STATUSES, default=0)
    status_message = models.CharField(max_length=512, default='')

    date_rent = models.DateTimeField(default=datetime.now, db_index=True, editable=False)
    date_prepared = models.DateTimeField(db_index=True, null=True, blank=True, editable=False)
    date_shipped = models.DateTimeField(db_index=True, null=True, blank=True)
    date_delivered = models.DateTimeField(db_index=True, null=True, blank=True, editable=False)
    date_shipped_back = models.DateTimeField(db_index=True, null=True, blank=True, editable=False)
    date_returned = models.DateTimeField(db_index=True, null=True, blank=True, editable=False)

    first_name = models.CharField('First Name', max_length=30, null=True, editable=False)
    last_name = models.CharField('Last Name', max_length=30, null=True, editable=False)

    shipping_address1 = models.CharField(max_length=255, verbose_name='Address 1', null=True, editable=False)
    shipping_address2 = models.CharField(max_length=255, verbose_name='Address 2', null=True, blank=True, editable=False)
    shipping_city = models.CharField(max_length=100, verbose_name='City', null=True, editable=False)
    shipping_state = models.CharField(max_length=2, verbose_name='State', null=True, editable=False)
    shipping_county = models.CharField(max_length=100, verbose_name='County', null=True, editable=False)
    shipping_zip_code = models.CharField(max_length=10, verbose_name='Zip', null=True, editable=False)

    outgoing_endicia_data = JSONField(null=True, editable=False)
    outgoing_mail_label = models.ImageField(upload_to='labels/%Y/%m/%d', null=True, editable=False)
    outgoing_tracking_number = models.CharField(max_length=50, null=True)
    outgoing_tracking_scans = JSONField(null=True, editable=False)

    incoming_endicia_data = JSONField(null=True, editable=False)
    incoming_mail_label = models.ImageField(upload_to='labels/%Y/%m/%d', null=True, editable=False)
    incoming_tracking_number = models.CharField(max_length=50, null=True)
    incoming_tracking_scans = JSONField(null=True, editable=False)

    source_dc = models.ForeignKey('inventory.Dropship', null=True, blank=True)
    inventory = models.ForeignKey('inventory.Inventory', null=True, blank=True)
    map = models.IntegerField(null=True)
    shipped_by = models.ForeignKey('auth.User', null=True, related_name='shipped_rent_orders')

    penalty_payment = models.OneToOneField(BillingHistory, null=True)
    next_penalty_check = models.DateTimeField(null=True)

    prepared_by = models.ForeignKey(User, null=True, related_name='prepared_games')
    return_accepted_by = models.ForeignKey(User, null=True, related_name='return_accepted_games')
    returned_to_dc = models.ForeignKey('inventory.Dropship', null=True, blank=True, related_name='returns')

    list_item = models.OneToOneField('RentList', null=True, related_name='rent_order')
    scanned_in_route = models.BooleanField(default=False, db_index=True)

    speed_2x = models.BooleanField(default=False)


    @staticmethod
    @transaction.commit_on_success
    def create(user, list_item, source_dc, status=RentOrderStatus.Pending):
        profile = user.get_profile()
        if profile.extra_rent_slots > 0:
            profile.extra_rent_slots -= 1
            profile.save()
            speed_2x = True
        else:
            speed_2x = False
        data = profile.get_name_data()
        data.update(profile.get_shipping_address_data(prefix='shipping'))
        order = RentOrder(user=user,
                          item=list_item.item,
                          status=status,
                          source_dc=source_dc,
                          map=list_item.weight,
                          list_item=list_item,
                          speed_2x=speed_2x,
                          **data)
        order.save()

        return order

    @staticmethod
    def list_stolen_games(user):
        oo = RentOrder.objects.filter(user=user,
                                      status__in=[RentOrderStatus.Shipped, RentOrderStatus.Claim],
                                      date_returned=None,
                                      scanned_in_route=False,
                                      penalty_payment=None,
                                      date_rent__gte=datetime(2010, 11, 01))
        return oo

    @staticmethod
    def buy_games_at_home(user, description='Plan Cancellation', penalty_reason=('CANC', 'Rent Cancellation')):
        def sale_item(order):
            logger.debug('Change status of %s to "Sale"', order)
            order.status = RentOrderStatus.Sale
            order.save()
            order.inventory.status = 5 # InventoryStatus.Sale
            order.inventory.save()

        profile = user.get_profile()
        description = '%s (outstanding game)' % description
        amount = decimal.Decimal('50.0')
        res = True
        for order in RentOrder.list_stolen_games(user):
            # if still not authorized for $50 try to do it now
            if not order.penalty_payment:
                order.take_penalty_payment(force=True, penalty_reason=penalty_reason)

            payment_taken = False
            # if $50 successfully charged...
            if order.penalty_payment:
                p = order.penalty_payment.capture()
                if p:
                    payment_taken = True
                    order.penalty_payment = p
                    # mark the order as 'sold'
                    sale_item(order)

            if not payment_taken: # if not, try to take store credits
                store_credits = profile.unlocked_store_credits
                if store_credits >= amount:
                    BillingHistory.create(user, 'Store Credits', description,
                        debit=amount, reason='rent', status=TransactionStatus.Passed,
                        type=TransactionType.RentPayment)

                    profile.withdraw_store_credits(amount, save=True)
                    # and mark the order as 'sold'
                    sale_item(order)
                else:
                    res = False
        return res


    def claims(self):
        from project.claims.models import Claim
        return Claim.list(self)

    def __unicode__(self):
        return 'Order #%s (%s)' % (self.order_no(), self.get_status_display())

    def order_no(self):
        return '%08d' % self.id

    def display_name(self):
        return ' '.join((self.first_name, self.last_name))

    def get_date_returned_disaplay(self):
        from django.template.defaultfilters import date
        if self.status in [RentOrderStatus.Canceled, RentOrderStatus.AutoCanceled, RentOrderStatus.AutoCanceledByAstral, RentOrderStatus.AutoCanceledByManualCheck]:
            return 'Canceled'
        if self.status == RentOrderStatus.Sale:
            return 'Sold'
        return date(self.date_returned)

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

    def __do_endicia_request(self, reply_postage, description, dropship):
        endicia = Endicia(**settings.ENDICIA_CONF)
        res = endicia.get_postage_label(
            type=LabelType.DestinationConfirm,
            size=LabelSize.Dymo30384,
            #image_rotation=ImageRotation.Rotate90,
            image_format=ImageFormat.GIF,
            mail_class=MailClass.First,
            date_advance=7,
            weight=3.5,
            mailpiece_shape=MailpieceShape.Letter,
            machinable=True,
            sort_type=SortType.SinglePiece,
            include_postage=True,
            show_return_address=False,
            reply_postage=reply_postage,
            stealth=False,
            signature_waiver=True,
            no_weekend_delivery=False,
            no_holiday_delivery=True,
            return_to_sender=True,
            barcode_format='PLATNET Code, 14',
            cost_center=1,
            description=description,
            reference_id='Rent',
            partner_customer_id='%08d' % self.user.id,
            partner_transaction_id='%08d' % self.id,
            to={
                'name': ' '.join((self.first_name, self.last_name)).upper(),
                'address1': self.shipping_address1.upper(),
                'address2': self.shipping_address2.upper(),
                'city': self.shipping_city.upper(),
                'state': self.shipping_state.upper(),
                'postal_code': split_zip(self.shipping_zip_code)[0],
                'zip4': split_zip(self.shipping_zip_code)[1],
                'delivery_point': '00',
            },
            frm={
                'name': 'GAMEMINE',
                'city': dropship.city.upper(),
                'state': dropship.state.upper(),
                'postal_code': dropship.postal_code.upper(),
                'zip4': split_zip(dropship.postal_code)[1].upper(),
            },
            return_address=dropship.address.upper(),
            postage_price = True)
        return res

    def request_outgoing_mail_label(self):
        """
        Queries and saves endicia outgoing mail label to model.
        Fields: ``outgoing_endicia_data``, ``outgoing_tracking_number``, ``outgoing_mail_label``.
        If data already in DB, returns (True, None).
        """
        if self.outgoing_tracking_number:
            return True, None
        res = self.__do_endicia_request(False, 'Rental Mailing Shipping Label', self.source_dc)
        logger.info('Creating outgoing label. Status: %s (%s)', res.Status, res.ErrorMessage if res.Status != '0' else 'OK')
        if res.Status == '0':
            self.outgoing_endicia_data = res._dict['LabelRequestResponse']
            self.outgoing_tracking_number = self.outgoing_endicia_data['PIC']
            label_file = ContentFile(base64.decodestring(res.Base64LabelImage))
            self.outgoing_mail_label.save('R%08do.gif' % self.id, label_file)
        else:
            self.outgoing_tracking_number = ''
            self.outgoing_endicia_data = ''
            try:
                self.outgoing_mail_label.delete(True)
            except OSError:
                pass
        return res.Status == '0', res.ErrorMessage if res.Status != '0' else 'OK'

    def request_incoming_mail_label(self):
        """
        Queries and saves endicia incoming mail label to model.
        Fields: ``incoming_endicia_data``, ``incoming_tracking_number``, ``incoming_mail_label``.
        If data already in DB, returns (True, None).
        """
        if self.incoming_tracking_number:
            return True, None
        res = self.__do_endicia_request(True, 'Rental Return Shipping Label', self.user.get_profile().dropship)
        logger.info('Creating incoming label. Status: %s (%s)', res.Status, res.ErrorMessage if res.Status != '0' else 'OK')
        if res.Status == '0':
            self.incoming_endicia_data = res._dict['LabelRequestResponse']
            self.incoming_tracking_number = self.incoming_endicia_data['PIC']
            label_file = ContentFile(base64.decodestring(res.Base64LabelImage))
            self.incoming_mail_label.save('R%08di.gif' % self.id, label_file)
        else:
            self.incoming_tracking_number = ''
            self.incoming_endicia_data = ''
            try:
                self.incoming_mail_label.delete(True)
            except:
                pass
        return res.Status == '0', res.ErrorMessage if res.Status != '0' else 'OK'

    @transaction.commit_on_success
    def mark_as_shipped(self, user=None, date=None):
        if self.status == RentOrderStatus.Shipped:
            return

        from project.inventory.models import InventoryStatus

        try:
            self.list_item.delete()
        except:
            pass
        self.list_item = None

        date = date or datetime.now()
        self.date_shipped = date
        self.status = RentOrderStatus.Shipped
        self.shipped_by = user
        self.save()
        self.inventory.status = InventoryStatus.Rented
        self.inventory.save()
        username = self.shipped_by.get_profile().get_name_display()
        self.add_event('Mailing Label shipped by %s from %s DC' % (username, self.source_dc.code))
        self.send_video_game_mailed_mail()


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
        return list(self.__get_tracking_scan(self.outgoing_tracking_scans))

    def get_return_tracking_scan(self):
        return list(self.__get_tracking_scan(self.incoming_tracking_scans))

    def add_event(self, action, comment=None, timestamp=None):
        e = RentOrderEvent(order=self, action=action, comment=comment)
        if timestamp:
            e.timestamp = timestamp
        e.save()
        return e

    def list_claims(self):
        from project.claims.models import Claim

        return Claim.list(self)

    def add_claim_event(self, claim, timestamp=None):
        e = RentOrderEvent(order=self, claim=claim)
        if timestamp:
            e.timestamp = timestamp
        e.save()
        return e

    """
        ticket#84:
        setting decrease_strike as false
        documentation was not clear and I didn't get the best information to apply the right fix, so
        after talking to michael, he told me to change the code just to fix this ticket and nothing else.
        this is the simplest way to resolve only this issue not affecting anything else is adding a decrease_strike parameter
    """
    def do_return(self, inventory_status=3, dc=None, user=None,decrease_strike=True):
        plan = MemberRentalPlan.get_current_plan(self.user)
        from project.crm.models import PersonalGameTicket, CaseStatus
        from project.inventory.models import InventoryStatus

        if inventory_status == InventoryStatus.Damaged:
            pass
        elif inventory_status == InventoryStatus.Lost:
            self.user.get_profile().inc_strikes(1)
        elif inventory_status == InventoryStatus.InStock and self.status == RentOrderStatus.Claim and decrease_strike:
            self.user.get_profile().inc_strikes(-1)
        else:
            if plan and plan.status == RentalPlanStatus.Suspended:
                plan.status = RentalPlanStatus.Active if plan.payment_fails_count == 0 else RentalPlanStatus.Delinquent
                plan.save()

        self.cancel_penalty_payment()
        self.status = RentOrderStatus.Returned
        self.date_returned = datetime.now()
        self.return_accepted_by = user
        self.returned_to_dc = dc
        self.save()
        self.inventory.status = inventory_status
        self.inventory.dropship = dc
        self.inventory.save()

        profile = self.user.get_profile()
        user_strikes = profile.strikes
        if plan and plan.status == RentalPlanStatus.Suspended and user_strikes < 3 and not plan.status is RentalPlanStatus.Delinquent:
                plan.set_status(RentalPlanStatus.Active)
        try:
            ticket = PersonalGameTicket.objects.exclude(status__in=[CaseStatus.Closed, CaseStatus.AutoClosed]).get(order=self)
            ticket.change_status(user, CaseStatus.AutoClosed, 'Game returned')
            if plan.status == RentalPlanStatus.PersonalGame:
                if PersonalGameTicket.objects.filter(order__user=user).exclude(status__in=[CaseStatus.AutoClosed, CaseStatus.Closed]).count() == 0:
                    plan.set_status(RentalPlanStatus.Active)
        except PersonalGameTicket.DoesNotExist:
            pass
        unreturned_games = RentOrder.objects.filter(user=self.user, status__in=[RentOrderStatus.Prepared, RentOrderStatus.Shipped])
        unreturned_games_count = unreturned_games.count()
        if unreturned_games_count == 0 and plan and plan.status in [RentalPlanStatus.Delinquent, RentalPlanStatus.Collection]:
            paid, aim_response = plan.take_delinquent_payment(True)
            if not paid or profile.strikes == 3:
                plan.set_status(RentalPlanStatus.Suspended,"Excessive Claims (3 Strikes), Fraud or Duplicate Account")
                plan.send_rent_account_suspension_email()
        self.send_video_game_received_mail()

    def get_lost_claim(self):
        from project.claims.models import DontReceiveClaim, SphereChoice
        claims = DontReceiveClaim.objects.filter(object_id=self.id, sphere_of_claim=SphereChoice.Rent)
        return claims[0] if claims else None

    def get_damaged_claim(self):
        from project.claims.models import GameIsDamagedClaim, SphereChoice
        claims = GameIsDamagedClaim.objects.filter(object_id=self.id, sphere_of_claim=SphereChoice.Rent)
        return claims[0] if claims else None

    def add_mail_tracking_scan_event(self, code):
        if code == 'A':
            self.add_event('Mailing Label scanned by the US Postal Service')
        elif code == 'D':
            self.add_event('Mailing Label delivered by the US Postal Service')
        elif code == 'I':
            self.add_event('Mailing Label scanned in route')
        elif code == 'R':
            self.send_address_hold_restriction_email()

    def add_return_tracking_scan_event(self, code):
        if code == 'A':
            self.add_event('Return mailer scanned by US Postal Service')
        elif code == 'D':
            self.add_event('Return mailer delivered by the US Postal Service')
        elif code == 'I':
            self.add_event('Mailing Label scanned in route')
        if code in ['A', 'D', 'I'] and not self.scanned_in_route:
            self.cancel_penalty_payment()
            self.scanned_in_route = True
            self.save()
            p = self.user.get_profile()
            p.extra_rent_slots += 1
            p.save()

    def send_address_hold_restriction_email(self):
        mail(self.user.email, 'emails/rent_emails/address_hold_restriction.html', {
            'order': self,
            'user': self.user,
        }, subject='Account Restricted - Confirm your Mailing Address')

    def send_video_game_mailed_mail(self):
        mail(self.user.email, 'emails/rent_emails/video_game_mailed.html', {
            'order': self,
            'user': self.user,
            'dc_name': self.source_dc.name,
        }, subject='"' + self.item.short_name + '" has been mailed')

    def send_video_game_received_mail(self):
        mail(self.user.email, 'emails/rent_emails/video_game_received.html', {
            'order': self,
            'user': self.user,
        }, subject='"' + self.item.short_name + '" has been received')


    def take_penalty_payment(self, force=False, penalty_reason=('CANC', 'Rent Cancellation')):
        if self.penalty_payment != None:
            return
        if not force and self.next_penalty_check and self.next_penalty_check > datetime.now():
            return
        aim = create_aim()
        profile = self.user.get_profile()
        card = profile.get_billing_card_data()
        data = {
            'amount': decimal.Decimal('50.0'),
            'number': card['number'],
            'exp': '/'.join(('%s' % card['exp_month'], ('%s' % card['exp_year'])[-2:])),
            'code': card['code'],
            'billing': profile.get_billing_data(),
            'shipping': profile.get_shipping_data(),
            'invoice_num': 'RENT_%s_%s_%s' % (penalty_reason[0], self.user.id, self.id),
            'description': '%s - Unreturned Game Fees' % penalty_reason[1],
            'x_email': self.user.email,
            'x_cust_id': self.user.id,
        }
        res = aim.authorize(**data)

        billing_history = BillingHistory(user=self.user,
                                         payment_method=profile.get_payment_card().display_number,
                                         description=data['description'],
                                         debit=data['amount'],
                                         reason='rent',
                                         type=TransactionType.RentPayment,
                                         status=TransactionStatus.Authorized,
                                         card_data=card,
                                         aim_transaction_id=res.transaction_id,
                                         aim_response=res._as_dict,
                                         message=res.response_reason_text)

        if res.response_code != 1:
            self.next_penalty_check = datetime.now() + timedelta(2)
            self.save()
            billing_history.status = TransactionStatus.Declined
            billing_history.save()
            return
        billing_history.save()
        self.penalty_payment = billing_history
        self.save()


    def cancel_penalty_payment(self):
        from project.claims.models import GameIsDamagedClaim, WrongGameClaim
        for c in itertools.chain(GameIsDamagedClaim.list(self), WrongGameClaim.list(self)):
            c.next_penalty_payment_date = None
            c.save()
            c.cancel_penalty_payment()

        if self.penalty_payment == None or self.penalty_payment.get_refund() or self.penalty_payment.status == TransactionStatus.Canceled:
            return
        if self.penalty_payment.is_setted():
            self.penalty_payment.refund_transaction(comment='Game Returned')
        else:
            self.penalty_payment.void_transaction()


    def put_back_to_list(self):
        if self.status != RentOrderStatus.Pending:
            return False
        if not self.list_item:
            for i, rl in enumerate(RentList.objects.filter(user=self.user), 1):
                rl.order = i
                rl.save()
            RentList(user=self.user, item=self.item).save()
        self.delete()
        return True


class RentOrderPoll(models.Model):
    order = models.OneToOneField(RentOrder)
    received_match_shipped = models.NullBooleanField(verbose_name='Does game received match shipped?')
    returned_personal_game = models.NullBooleanField(verbose_name='Member returned a personal game?')
    is_damaged = models.NullBooleanField(verbose_name='Game received is damaged?')
    game_broken = models.BooleanField(verbose_name='Broken', default=False)
    game_unplayable = models.BooleanField(verbose_name='Unplayable', default=False)
    game_missing = models.BooleanField(verbose_name='Missing', default=False)
    message = models.TextField(null=True, blank=True)


def write_event(sender, instance, created, **kwargs):
    from project.claims.models import Claim

    if not created or not isinstance(instance, Claim) or not isinstance(instance.claim_object, RentOrder):
        return
    order = instance.claim_object
    order.add_claim_event(instance)
signals.post_save.connect(write_event, None)


class RentOrderEvent(models.Model):
    class Meta:
        ordering = ['timestamp']

    order = models.ForeignKey('RentOrder', related_name='events')
    action = models.CharField(max_length=256, null=True)
    claim = models.ForeignKey('claims.Claim', null=True)
    timestamp = models.DateTimeField(default=datetime.now, db_index=True)
    comment = models.CharField(max_length=512, null=True)

    def get_action_display(self):
        if self.action:
            return self.action
        if self.claim:
            return mark_safe('Member submits <strong>"%s"</strong> claim' % self.claim.get_title())


class RentList(models.Model):
    """
    ``RentList`` represents ``Item`` in user's rent list.
    XXX(Roman): May be a better name should be ``RentItem``.

    Fields:
    ``order``: item order in the rent list
    ``weight``: is calculated by ``RentAllocationMatrix.calculate_weight()``
    """
    class Meta:
        ordering = ['order', 'added']

    user = models.ForeignKey(User, null=True)
    session_id = models.CharField(max_length=50, null=True, db_index=True)
    item = models.ForeignKey('catalog.Item')
    added = models.DateTimeField(default=datetime.now, db_index=True)
    order = models.IntegerField(default=0, db_index=True)
    notes = models.TextField(default='')
    weight = models.IntegerField(default=0, db_index=True)

    @staticmethod
    def get_priority1():
        """
        Returns rent items with Priority #1 for active rental plans
        """
        sql = '''
            SELECT
                l.*
            FROM
                rent_rentlist l
                    left outer join rent_memberrentalplan rp on (l.user_id = rp.user_id)
                    left outer join rent_rentalplan p on (p.plan = rp.plan)
                    left outer join members_profile pp on (l.user_id = pp.user_id)
            WHERE
                l.id = (select l2.id from rent_rentlist l2 where l2.user_id = l.user_id AND not exists (SELECT * FROM rent_rentorder ro WHERE ro.list_item_id = l2.id) order by "order", added limit 1)
                AND rp.status in (0, 1)
                AND rp.cancel_confirmation_code is null
                AND l.user_id is not null
                AND (p.games_allowed + pp.extra_rent_slots) > (select count(1) from rent_rentorder ro where ro.user_id = l.user_id and ro.status in (0, 1, 4))
            ORDER BY weight DESC, added;'''
        return RentList.objects.raw(sql)

    @staticmethod
    @transaction.commit_on_success
    def add_to_list(request, item, first_position=False):
        list_filter = {}
        if request.user.is_authenticated():
            list_filter['user'] = request.user
            qs = RentOrder.objects.filter(
                user=request.user,
                item=item,
                status__in=[
                    RentOrderStatus.Shipped,
                    RentOrderStatus.Pending,
                    RentOrderStatus.Prepared
                ]
            )
            if qs.count() > 0:
                return -1
        else:
            list_filter['session_id'] = request.current_session_id

        def find_position(list_filter, item):
            for index, i in itertools.izip(itertools.count(1), RentList.objects.filter(**list_filter)):
                if i.item.id == item.id:
                    return index
            return None

        def move_to_first(list_filter, item):
            q = RentList.objects.filter(**list_filter).exclude(item=item)
            for order, i in itertools.izip(itertools.count(2), q):
                i.order = order
                i.save()
            i = RentList.objects.get(item=item, **list_filter)
            i.order = 1
            i.save()
            return 1

        if RentList.objects.filter(item=item, **list_filter).count() == 0:
            count = RentList.objects.filter(**list_filter).count()
            RentList(item=item, order=count+1, **list_filter).save()
        if not first_position:
            return find_position(list_filter, item)
        return move_to_first(list_filter, item)

    @staticmethod
    def get(user=None, request=None, available=False):
        filter = {}
        if request:
            if request.user.is_authenticated():
                filter['user'] = request.user
                for item in RentList.objects.filter(user=None, session_id=request.current_session_id):
                    if RentList.objects.filter(user=request.user, item=item.item).count() == 0:
                        item.user = request.user
                        item.session_id = None
                        item.save()
                    else:
                        item.delete()
            else:
                filter['session_id'] = request.current_session_id
        else:
            filter['user'] = user
        qs = RentList.objects.filter(**filter)
        if available:
            qs = qs.filter(item__rent_flag=True)
        return qs

    @staticmethod
    def pending_list():
        res = []
        for user in User.objects.filter(is_active=True):
            plan = MemberRentalPlan.get_current_plan(user)
            if plan:
                res += plan.get_pending_items()
        return res

    @staticmethod
    def purge():
        date_x = datetime.now().date() - timedelta(1)
        qs = RentList.objects.filter(added__lt=date_x, user=None)
        logger.debug('Going to purge %d rent list items...', qs.count())
        qs.delete()


    @staticmethod
    def find_position(request, item):
        for index, i in itertools.izip(itertools.count(1), RentList.get(request=request)):
            if i.item.id == item.id:
                return index
        return None

def rental_plan_post_save(sender, instance, created, **kwargs):
    RentalPlan.clear_cache()
signals.post_save.connect(rental_plan_post_save, RentalPlan)


ALLOCATION_FACTORS = (
    ('account_type_special_promo_code', 'Account Type (Special - Promo Code)'),
    ('account_type_no_special_promo_code', 'Account Type (Standard - No Promo Code)'),

    ('buy_threshold_a', 'Buy Threshold-A (1 to 2 in past 30-days with total value of $30)'),
    ('buy_threshold_b', 'Buy Threshold-B (3 to 4 in past 30-days with total value of $40)'),
    ('buy_threshold_c', 'Buy Threshold-C (5 to 6 in past 60-days with total value of $50)'),
    ('buy_threshold_d', 'Buy Threshold-D (7+ in past 60-days with total value of $60)'),

    ('trade_threshold_a', 'Trade Threshold-A (2 to 3 in past 30-days with average value of $20)'),
    ('trade_threshold_b', 'Trade Threshold-B (4 to 5 in past 30-days with average value of $25)'),
    ('trade_threshold_c', 'Trade Threshold-C (5 to 7 in past 30-days with average value of $30)'),
    ('trade_threshold_d', 'Trade Threshold-D (7+ in past 30-days with average value of $35)'),

    ('rental_threshold_a', 'Rental Threshold-A (7 or more in past 30-days)'),
    ('rental_threshold_b', 'Rental Threshold-B (4 to 6 in past 30-days)'),
    ('rental_threshold_c', 'Rental Threshold-C (1 to 3 in past 30-days)'),
    ('rental_threshold_d', 'Rental Threshold-D (0 in past 30-days)'),

    ('declined_rental_billing_status_a', 'Declined Rental Billing Status (1 to 2)'),
    ('declined_rental_billing_status_b', 'Declined Rental Billing Status (3+)'),

    ('last_game_shipped_a', 'Last Game Shipped (0-1 days)'),
    ('last_game_shipped_b', 'Last Game Shipped (2-3 days)'),
    ('last_game_shipped_c', 'Last Game Shipped (4+ days)'),

    ('claim_threshold_a', 'Claim Threshold-A (0 in past 30-days)'),
    ('claim_threshold_b', 'Claim Threshold-B (1 in past 30-days)'),
    ('claim_threshold_c', 'Claim Threshold-D (2 or more in past 30-days)'),

    ('dc_transfer_threshold_a', 'DC Transfer Threshold-A (0 in past 30-days)'),
    ('dc_transfer_threshold_b', 'DC Transfer Threshold-B (1 to 2 in past 30-days)'),
    ('dc_transfer_threshold_c', 'DC Transfer Threshold-C (3+ in past 30-days)'),

    ('last_priority_shipped_threshold_a', 'Last Priority Shipped Threshold-A (ranking 1 to 3)'),
    ('last_priority_shipped_threshold_b', 'Last Priority Shipped Threshold-B (ranking 4 to 6)'),
    ('last_priority_shipped_threshold_c', 'Last Priority Shipped Threshold-C (ranking 7+)'),

    ('queue_priority_rank_a', 'Queue Priority Rank (games is between 1 and 3)'),
    ('queue_priority_rank_b', 'Queue Priority Rank (games is between 4 and 10)'),
    ('queue_priority_rank_c', 'Queue Priority Rank (games is between 11 or more)'),

    ('membership_tenure_a', 'Membership Tenure (181 days or more old)'),
    ('membership_tenure_b', 'Membership Tenure (between 91 and 180 days old)'),
    ('membership_tenure_c', 'Membership Tenure (between 31 and 90 days old)'),
    ('membership_tenure_d', 'Membership Tenure (between 1 and 30 days old)'),
)


class AllocationFactor(models.Model):
    key = models.CharField(max_length=50, primary_key=True, choices=ALLOCATION_FACTORS)
    value = models.IntegerField(blank=True, default=0)
