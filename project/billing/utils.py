import logging

from django.contrib.auth.models import User

from project.utils import create_aim
from project.members.models import BillingHistory, TransactionType, TransactionStatus
from project.taxes.utils import get_tax_amount
from project.utils.mailer import mail

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


def create_aim_data(amount, invoice_num, description, profile):
    """
    Helper function, creates aim_data dictionary, needed for ``authorizenet.aim.AIM`` methods
    """
    card = profile.billing_card

    aim_data = {
        'number': card.data['number'],
        'exp': '/'.join(('%s' % card.data['exp_month'], ('%s' % card.data['exp_year'])[-2:])),
        'code': card.data['code'],
        'shipping': profile.get_shipping_data(),
        'billing': profile.get_billing_data(),
        'invoice_num': invoice_num,
        'description': description,
        'x_email': profile.user.email,
        'x_cust_id': profile.user.id,
    }

    return aim_data


def withdraw_store_credits(profile, amount):
    """
    Helper function, withdraws $ ``amount`` from user's store credits.
    If not enough store credits, just withdraws all.
    Returns amount of credits withdrawn.
    """
    if profile.unlocked_store_credits < amount:
        amount = profile.unlocked_store_credits
    profile.withdraw_store_credits(amount)
    return amount


def _create_billing_history(billing_history, profile, amount, tax_amount, description,
                            withdrawed_credits, aim_response=None):
    """
    Helper function, updates ``BillingHistory`` instance.
    """
    if not tax_amount:
        tax_amount = None
    billing_history.card_data = profile.get_billing_card_data()
    billing_history.tax = tax_amount
    billing_history.description = description
    if aim_response:
        billing_history.debit = amount
        billing_history.aim_transaction_id = aim_response.transaction_id
        billing_history.aim_response = aim_response._as_dict
        billing_history.message = aim_response.response_reason_text
        if aim_response.response_code != 1:
            billing_history.status = TransactionStatus.Declined
    if withdrawed_credits:
        billing_history.applied_credits = withdrawed_credits
        billing_history.debit = amount
    billing_history.save()
    return billing_history


def get_profile(user_or_profile):
    if isinstance(user_or_profile, User):
        return user_or_profile.get_profile()
    else:
        return user_or_profile


def send_billing_charge_approved(user_or_profile, amount):
        profile = get_profile(user_or_profile)
        mail(profile.email, 'billing/emails/billing_charge_approved.html', {
            'plan': profile.member_rental_plan,
            'user': profile.user,
            'cc_type': profile.billing_card.get_type_display(),
            'cc_num': profile.billing_card.data['number'][-4:],
            'amount': amount,
        }, subject='Gamemine - Billing Charge Approved')


def take_money(user_or_profile, amount, reason,
                invoice_num_func=None, description=None,
                take_tax=True, take_credits=True, payment_type="AUTH_CAPTURE"):
    """
    Takes money from user's CC and / or store credits.

    *Args*:
    ``amount``: e. g. Decimal('13.95')
    ``reason``: e. g. 'rent'
    ``invoice_num_func``: function that takes ``profile`` and ``billing_history``,
                            and returns ``invoice_num`` (e. g. 'RENT_SUBS_1_2')
    ``description``: e. g. 'Monthly Membership - Nov 5, 2011 - Dec 5, 2011'
    """
    profile = get_profile(user_or_profile)
    card = profile.billing_card
    aim_method = {
        "AUTH_CAPTURE": "capture"
    }[payment_type]
    tax_amount = 0
    if take_tax:
        tax_amount = get_tax_amount(amount, card.state, card.county)

    withdrawed_credits = withdraw_store_credits(profile, amount)
    logger.debug('Taking $%s store credits...', withdrawed_credits)
    amount -= withdrawed_credits
    aim_response = None

    billing_history = BillingHistory.create(
        profile.user, profile.get_billing_card_display(),
        debit=amount, reason=reason, type=TransactionType.RentPayment
    )

    if amount:
        logger.debug('Taking amount of $%s (+$%s tax)...', amount, tax_amount)
        aim = create_aim()
        invoice_num = invoice_num_func(profile, billing_history)
        aim_data = create_aim_data(amount, invoice_num, description, profile)
        aim_response = getattr(aim, aim_method)(amount, **aim_data)
        logger.debug('AIM aim_responseponse code: %s (%s)', aim_response.response_code, aim_response.response_reason_code)

    _create_billing_history(billing_history, profile, amount, tax_amount,
                            description, withdrawed_credits, aim_response)

    if amount:
        if aim_response.response_code != 1:
            if aim_response.response_code == 3 and aim_response.response_reason_code in [6, 7, 8]:
                raise PaymentError("Credit card is expired")
            elif aim_response.response_reason_code in [2, 3, 4]:
                raise PaymentError("Insufficient funds are available for this transaction.")
            elif aim_response.avs_response == "U":
                raise PaymentError("We do not accept prepaid cards.")
            else:
                raise PaymentError("We are unable to process you credit card at this time.")

    send_billing_charge_approved(profile, amount)

    return aim_response
