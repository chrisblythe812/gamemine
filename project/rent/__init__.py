from logging import debug
import itertools


def get_minimal_rent_charge():
    from project.new_rent.models import RentalPlan
    return RentalPlan.objects.get(slug="unlimited1").first_payment_amount


def list_games_at_home(user):
    if user and user.is_authenticated():
        from models import RentOrder, RentOrderStatus
        qs = RentOrder.objects.filter(status__in=[RentOrderStatus.Shipped, RentOrderStatus.Pending, RentOrderStatus.Prepared]).filter(user=user)
        return itertools.imap(lambda x: x.item, qs)
    else:
        return []

def is_item_at_home(item, user):
    if not user or not user.is_authenticated():
        return False
    from models import RentOrder, RentOrderStatus
    qs = RentOrder.objects.filter(status__in=[RentOrderStatus.Shipped])
    return qs.filter(user=user, item=item).count() > 0


def is_item_at_shipping_process(item, user):
    if not user or not user.is_authenticated():
        return False
    from models import RentOrder, RentOrderStatus
    qs = RentOrder.objects.filter(status__in=[RentOrderStatus.Pending, RentOrderStatus.Prepared])
    return qs.filter(user=user, item=item).count() > 0


def is_item_on_list(item, user):
    if not user or not user.is_authenticated():
        return False
    from models import RentList
    qs = RentList.objects.filter(user=user, item=item)
    return qs.count() > 0
