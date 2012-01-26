import datetime
from decimal import Decimal

from django_snippets.utils.datetime import inc_date

from project.utils import create_aim
from project.members.utils import build_aim_data
from project.members.utils import get_card_display_number
from project.taxes.utils import get_tax_amount
from project.members.models import (
    BillingHistory, TransactionStatus, TransactionType)
from project.billing.utils import PaymentError


class RentalPlanBillingMixin(object):
    def get_prices(self):
        return self.first_payment_amount, self.thereafter_payments_amount

    def get_next_payment(self, plan_start_date=None, force_future_date=False):
        if force_future_date:
            raise NotImplementedError
        payment_amount = self.thereafter_payments_amount
        payment_type = "AUTH_CAPTURE"
        pay_every = self.pay_every

        # If first payment
        if plan_start_date is None:
            plan_start_date = datetime.date.today()
            pay_every = 0
            payment_amount = self.first_payment_amount
            payment_type = self.first_payment_type

        if pay_every is None and payment_amount is None:
            return None, None, None

        while True:
            date, amount, type_ = inc_date(plan_start_date, pay_every), payment_amount, payment_type
            if not force_future_date or date > datetime.date.today():
                break
            plan_start_date = date
        return date, amount and Decimal(amount), type_

    def get_next_payment_date(self, plan_start_date=None, force_future_date=False):
        return self.get_next_payment(plan_start_date, force_future_date)[0]

    def get_next_payment_amount(self, plan_start_date=None, force_future_date=False):
        return self.get_next_payment(plan_start_date, force_future_date)[1]

    def get_next_payment_type(self, plan_start_date=None, force_future_date=False):
        return self.get_next_payment(plan_start_date, force_future_date)[2]

    def get_first_payment_description(self, trans_id):
        def format_date(date_):
            from django.template.defaultfilters import date
            return date(date_, 'M j, Y')

        invoice_num = 'RENT_NEW_%s' % trans_id
        today = datetime.date.today()
        next_payment_date = self.get_next_payment_date(today)

        description = "Monthly Membership - %s - %s" % (
            format_date(today), format_date(next_payment_date))

        return invoice_num, description

    def make_first_payment(self, user, profile, billing_card, customer_ip):
        """
        Being used when we would like to bill user for the first time and he doesn't
        have ``MemberRentalPlan`` associated yet.

        May raise ``PaymentError``.
        """
        billing_data = {
            "first_name": billing_card.first_name,
            "last_name": billing_card.last_name,
            "address1": billing_card.address1,
            "address2": billing_card.address2,
            "city": billing_card.city,
            "state": billing_card.state,
            "county": billing_card.county,
            "zip_code": billing_card.zip,
        }
        billing_card_data = billing_card.data.copy()
        shipping_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "address1": profile.shipping_address1,
            "address2": profile.shipping_address2,
            "city": profile.shipping_city,
            "state": profile.shipping_state,
            "county": profile.shipping_county,
            "zip_code": profile.shipping_zip,
        }
        email = user.email

        first_payment_amount = self.get_next_payment_amount()
        first_payment_type = self.get_next_payment_type()
        tax_amount = get_tax_amount(
            first_payment_amount, billing_data["state"], billing_data.get("county"))

        billing_history = BillingHistory.objects.create(
            payment_method=get_card_display_number(billing_card_data["number"]),
            debit=Decimal(first_payment_amount),
            reason="rent",
            type=TransactionType.RentPayment,
            card_data=billing_card_data,
            tax=tax_amount
        )

        invoice_num, description = self.get_first_payment_description(billing_history.pk)
        aim_data = build_aim_data(
            shipping_data, billing_data, billing_card_data,
            invoice_num, description, email, customer_ip, tax_amount
           )

        aim = create_aim()
        success_status = TransactionStatus.Passed
        if first_payment_type == "AUTH_ONLY":
            aim_response = aim.authorize(first_payment_amount, **aim_data)
            success_status = TransactionStatus.Authorized
        elif first_payment_type == "AUTH_CAPTURE":
            aim_response = aim.capture(first_payment_amount, **aim_data)

        billing_history.description = description
        billing_history.aim_transaction_id = aim_response.transaction_id
        billing_history.aim_response = aim_response._as_dict
        billing_history.message = aim_response.response_reason_text
        if aim_response.response_code == 1:
            billing_history.status = success_status
            billing_history.save()
            return billing_history
        else:
            billing_history.status = TransactionStatus.Declined
            billing_history.save()
            raise PaymentError(aim_response.response_reason_text)
