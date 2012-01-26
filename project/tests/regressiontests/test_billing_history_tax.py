import datetime

from django.test import TestCase
from django.core.management import call_command

from fudge import Fake, patched_context

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.models import MemberRentalPlan, RentalPlan
from project.members.models import BillingHistory, BillingCard
from project.taxes.utils import get_tax_amount


class BillingHistoryTests(TestCase, SignUpTestCase):
    def test_tax(self):
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        billing_card = BillingCard.objects.all()[0]
        billing_card.county = "Palm Beach"
        billing_card.save()
        mrp = MemberRentalPlan.objects.all()[0]
        fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            call_command("rent", "recurring_billing")
        self.assertEqual(BillingHistory.objects.count(), 2)
        bh = BillingHistory.objects.all()[1]
        self.assertEqual(bh.debit, plan.thereafter_payments_amount)
        self.assertEqual(bh.tax, get_tax_amount(plan.thereafter_payments_amount, state="FL", county="Palm Beach"))
