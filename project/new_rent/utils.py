import datetime

from project.new_rent.models import (
    MemberRentalPlan, RentalPlan, RentalPlanStatus, RentOrder, RentOrderStatus)
from project.billing.utils import take_money


#==============================================================================
# Change Plan
#==============================================================================
def get_payment_invoice_num(*args):
    """
    E. g. usage:
    >>> reason1 = "rent"
    >>> reason2 = "chng"
    >>> user_id = 1
    >>> trans_id = 5
    >>> get_payment_invoice_num(reason1, reason2, user_id, trans_id) == "RENT_CHNG_1_5"
    True
    """
    return "_".join([str(arg).upper() for arg in args])


def upgrade_plan(member_rental_plan, new_plan):
    """
    Upgrades current plan to ``new_plan``.
    """
    user = member_rental_plan.user
    amount = get_charge_for_the_rest_of_month(member_rental_plan, new_plan)

    def invoice_num_func(profile, billing_history):
        return get_payment_invoice_num(
            'rent', 'chng', profile.user.pk, billing_history.pk)
    take_money(
        user_or_profile=user,
        amount=amount,
        reason='rent',
        invoice_num_func=invoice_num_func,
        description="Change Rental Plan",
    )

    member_rental_plan.delete()
    new_mrp = MemberRentalPlan.objects.create(
        user=user,
        plan=new_plan.pk,
        status=RentalPlanStatus.Active,
        start_date=datetime.date.today(),
    )
    new_mrp.next_payment_date, new_mrp.next_payment_amount, _ = \
            new_mrp.rental_plan.get_next_payment(member_rental_plan.start_date)
    new_mrp.save()

    return new_mrp


def downgrade_plan(member_rental_plan, new_plan):
    """
    Downgrades current plan to ``new_plan``.
    """
    member_rental_plan.scheduled_rental_plan = new_plan
    member_rental_plan.save()
    return member_rental_plan


def get_charge_for_the_rest_of_month(member_rental_plan, new_plan):
    if isinstance(member_rental_plan, MemberRentalPlan):
        old_plan = member_rental_plan.rental_plan
    elif isinstance(member_rental_plan, RentalPlan):
        old_plan = member_rental_plan
    charge = (new_plan.thereafter_payments_amount -
                old_plan.thereafter_payments_amount)
    if charge <= 0:
        return 0
    return charge


def change_plan(member_rental_plan, new_plan):
    """
    Helper function to change member rental plan

    *Args:*
    ``member_rental_plan``: ``MemberRentalPlan`` instance
    ``new_plan``: RentalPlanS instance
    """
    if member_rental_plan.rental_plan.is_upgrade(new_plan):
        new_mrp = upgrade_plan(member_rental_plan, new_plan)

        # Updating orders rent dates, I don't know why do we need this
        orders = RentOrder.objects.filter(
                    user=new_mrp.user,
                    status__in=[RentOrderStatus.Pending, RentOrderStatus.Prepared])
        for order in orders:
            order.date_rent = datetime.now()
            order.save()
        # --
    else:
        new_mrp = downgrade_plan(member_rental_plan, new_plan)

    return new_mrp
#------------------------------------------------------------------------------


#==============================================================================
# Sign Up
#==============================================================================
def rent_signup_for_member(request, rental_plan_form, profile_user_form, billing_form):
    user_form, profile_form = profile_user_form.forms
    rental_plan = rental_plan_form.cleaned_data["rental_plan"]
    user = user_form.save()
    profile = profile_form.save()
    billing_card = billing_form.save(commit=False)
    billing_card.user = profile.user
    billing_card.save()
    customer_ip = request.META.get("REMOTE_ADDR")

    first_payment = rental_plan.make_first_payment(
        user,
        profile,
        billing_card,
        customer_ip
    )

    first_payment.user = profile.user
    first_payment.save()
    next_payment_date, next_payment_amount, next_payment_type = \
        rental_plan.get_next_payment(datetime.date.today())

    scheduled_plan = rental_plan.slug == "free_trial" and RentalPlan.PlanB or None

    member_rental_plan = MemberRentalPlan.objects.create(
        user=profile.user,
        plan=rental_plan.pk,
        status=RentalPlanStatus.Active,
        start_date=datetime.datetime.now(),
        expiration_date=rental_plan.get_expiration_date(),
        next_payment_date=next_payment_date,
        next_payment_amount=next_payment_amount,
        next_payment_type=next_payment_type,
        first_payment=first_payment,
        scheduled_plan=scheduled_plan
    )

    return member_rental_plan


def rent_signup_for_new_user(request, rental_plan_form, profile_user_form, billing_form):
    user_form, profile_form = profile_user_form.forms
    rental_plan = rental_plan_form.cleaned_data["rental_plan"]
    user = user_form.save(commit=False)
    profile = profile_form.save(commit=False)
    billing_card = billing_form.save(commit=False)
    customer_ip = request.META.get("REMOTE_ADDR")

    first_payment = rental_plan.make_first_payment(
        user,
        profile,
        billing_card,
        customer_ip
    )

    user.save()
    profile.user = user
    profile.save()
    billing_card.user = user
    billing_card.save()
    first_payment.user = profile.user
    first_payment.save()
    next_payment_date, next_payment_amount, next_payment_type = \
        rental_plan.get_next_payment(datetime.date.today())

    scheduled_plan = None
    if rental_plan.next_plan:
        scheduled_plan = rental_plan.next_plan.pk

    member_rental_plan = MemberRentalPlan.objects.create(
        user=profile.user,
        plan=rental_plan.pk,
        status=RentalPlanStatus.Active,
        start_date=datetime.datetime.now(),
        expiration_date=rental_plan.get_expiration_date(),
        next_payment_date=next_payment_date,
        next_payment_amount=next_payment_amount,
        next_payment_type=next_payment_type,
        first_payment=first_payment,
        scheduled_plan=scheduled_plan
    )

    return member_rental_plan
#------------------------------------------------------------------------------
