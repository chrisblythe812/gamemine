import itertools
from logging import debug
from datetime import datetime, timedelta

from django.db.models import Sum

from project.rent.models import RentOrder, RentOrderStatus, RentList,\
    AllocationFactor, MemberRentalPlan
from project.members.models import BillingHistory, TransactionStatus,\
    TransactionType
from project.claims.models import Claim
from project.buy_orders.models import BuyOrder, BuyOrderStatus


def _get_value(k):
    v = AllocationFactor.objects.get(key=k).value
    return v


class RentAllocationMatrixWeigher:
    @staticmethod
    def _promo_code(rent_item):
        if False:
            return _get_value('account_type_special_promo_code')
        return _get_value('account_type_no_special_promo_code')

    @staticmethod
    def _buy_threshold(rent_item):
        qs = BuyOrder.objects.filter(user=rent_item.user, status__in=[BuyOrderStatus.Delivered, BuyOrderStatus.Shipped])
        def get_stat(days):
            date_x = datetime.now().date() - timedelta(days)
            r = qs.filter(create_date__gte=date_x).aggregate(Sum('size'), Sum('total'))
            return r['size__sum'] or 0, r['total__sum'] or 0
        size, value = get_stat(60)
        if size >=7 and value >= 60: return _get_value('buy_threshold_d')
        if size >=5 and value >= 50: return _get_value('buy_threshold_c')
        size, value = get_stat(30)
        if size >=3 and value >= 40: return _get_value('buy_threshold_b')
        if size >=1 and value >= 30: return _get_value('buy_threshold_a')
        return 0

    @staticmethod
    def _trade_threshold(rent_item):
#    'trade_threshold_a': 1, # Trade Threshold-A (2 to 3 in past 30-days with average value of $20)
#    'trade_threshold_b': 2, # Trade Threshold-B (4 to 5 in past 30-days with average value of $25)
#    'trade_threshold_c': 3, # Trade Threshold-C (5 to 7 in past 30-days with average value of $30)
#    'trade_threshold_d': 4, # Trade Threshold-D (7+ in past 30-days with average value of $35)
        return 0

    @staticmethod
    def _rental_threshold(rent_item):
        date_x = datetime.now() - timedelta(30)
        qs = RentOrder.objects.filter(user=rent_item.user,
                                      date_rent__gt=date_x, 
                                      status__in=[RentOrderStatus.Shipped, RentOrderStatus.Shipped])
        count = qs.count()
        if count >= 7: return _get_value('rental_threshold_a')
        if count >= 4: return _get_value('rental_threshold_b')
        if count >= 1: return _get_value('rental_threshold_c')
        return _get_value('rental_threshold_d')

    @staticmethod
    def _declined_rental_billing_status(rent_item):
        qs = BillingHistory.objects.filter(user=rent_item.user,
                                           type=TransactionType.RentPayment,
                                           status=TransactionStatus.Declined)
        count = qs.count()
        if count == 0: return 0
        if count <= 2: _get_value('declined_rental_billing_status_a')
        return _get_value('declined_rental_billing_status_b')

    @staticmethod
    def _last_game_shipped(rent_item):
        d = datetime.now()
        for o in RentOrder.objects.filter(user=rent_item.user).order_by('-date_shipped'):
            d = o.date_shipped or datetime.now() 
            break
        d = (datetime.now() - d).days
        if d <= 1: return _get_value('last_game_shipped_a')
        if d <= 3: return _get_value('last_game_shipped_b')
        return _get_value('last_game_shipped_c')

    @staticmethod
    def _claim_threshold(rent_item):
        date_x = datetime.now().date() - timedelta(30)
        claims_count = Claim.objects.filter(user=rent_item.user, date__gte=date_x).count()
        if claims_count == 0: return _get_value('claim_threshold_a')
        if claims_count == 1: return _get_value('claim_threshold_b')
        return _get_value('claim_threshold_c')

    @staticmethod
    def _dc_transfer_threshold(rent_item):
#    'dc_transfer_threshold_a': 0, # DC Transfer Threshold-A (0 in past 30-days)
#    'dc_transfer_threshold_b': 2, # DC Transfer Threshold-B (1 to 2 in past 30-days)
#    'dc_transfer_threshold_c': 3, # #DC Transfer Threshold-C (3+ in past 30-days)
        return 0

    @staticmethod
    def _last_priority_shipped_threshold(rent_item):
#    'last_priority_shipped_threshold_a': 0, # Last Priority Shipped Threshold-A (ranking 1 to 3)
#    'last_priority_shipped_threshold_b': 2, # Last Priority Shipped Threshold-B (ranking 4 to 6)
#    'last_priority_shipped_threshold_c': 3, # Last Priority Shipped Threshold-C (ranking 7+)
        return 0

    @staticmethod
    def _queue_priority_rank(rent_item):
#    'queue_priority_rank_a': 4, # Queue Priority Rank (games is between 1 and 3)
#    'queue_priority_rank_b': 2, # Queue Priority Rank (games is between 4 and 10)
#    'queue_priority_rank_c': 0, # Queue Priority Rank (games is between 11 or more)
        return 0

    @staticmethod
    def _membership_tenure(rent_item):
        d = (datetime.now() - rent_item.user.date_joined).days
        if d >= 181: return _get_value('membership_tenure_a')
        if d >= 91: return _get_value('membership_tenure_b')
        if d >= 31: return _get_value('membership_tenure_c')
        return _get_value('membership_tenure_d')


class RentAllocationMatrix:
    @staticmethod
    def calculate_weight(rent_item):
        """
        Calculates weight for ``RentList`` instance based on rent allocation
        weights (e.g. ``RentAllocationMatrixWeigher._promo_code()``,
        ``RentAllocationMatrixWeigher._buy_threshold()``)

        Arguments:
        - ``rent_item``: ``RentList`` instance
        """
        if not rent_item.user:
            return -9999

        weight = 0
        weight += RentAllocationMatrixWeigher._promo_code(rent_item)
        weight += RentAllocationMatrixWeigher._buy_threshold(rent_item)
        weight += RentAllocationMatrixWeigher._trade_threshold(rent_item)
        weight += RentAllocationMatrixWeigher._rental_threshold(rent_item)
        weight += RentAllocationMatrixWeigher._declined_rental_billing_status(rent_item)
        weight += RentAllocationMatrixWeigher._last_game_shipped(rent_item)
        weight += RentAllocationMatrixWeigher._claim_threshold(rent_item)
        weight += RentAllocationMatrixWeigher._dc_transfer_threshold(rent_item)
        weight += RentAllocationMatrixWeigher._last_priority_shipped_threshold(rent_item)
        weight += RentAllocationMatrixWeigher._queue_priority_rank(rent_item)
        weight += RentAllocationMatrixWeigher._membership_tenure(rent_item)
        return weight

    @staticmethod
    def process_item(rent_list_item):
        """
        Blah
        """
        user = rent_list_item.user

        profile = user.get_profile()
        zip_code = profile.shipping_zip
        rent_list = RentList.objects.filter(user=user, rent_order=None)

        def chain_objects(o1, objects=[]):
            return itertools.chain([o1] if o1 else [], itertools.ifilter(lambda x: x != o1, objects))

        debug('Home DC: %s', profile.dropship)

        from project.inventory.models import Dropship
        dropships = list(chain_objects(profile.dropship, Dropship.list_by_distance(zip_code)))

        def find_dropship(item):
            for dropship in dropships:
                if dropship.is_game_available(item, for_rent=True):
                    return dropship
            return None

        rent_plan = MemberRentalPlan.get_current_plan(user)

        for list_item in chain_objects(rent_list_item, rent_list):
            dc = find_dropship(list_item.item)

            debug('Processing: %s %s...', list_item.user, list_item.item, )

            if not dc:
                #TODO: Create report 
                debug('Create report')
                continue

            if not rent_plan.is_valid():
                return False

            order = RentOrder.create(user, list_item, dc)
            debug('Rent order was created: %s', order)
            return True

        return False
