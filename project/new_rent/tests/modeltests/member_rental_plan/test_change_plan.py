import datetime

from django.test import TestCase
from django.core.management import call_command
from fudge import Fake, patched_context

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.models import MemberRentalPlan, RentalPlan
from project.new_rent.utils import change_plan
from project.members.models import BillingHistory
from project.rent.models import MemberRentalPlanHistory


class ChangePlanTests(TestCase, SignUpTestCase):
    def test_upgrade(self):
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        new_plan = RentalPlan.objects.get(slug="unlimited2")
        mrp = MemberRentalPlan.objects.all()[0]
        change_plan(mrp, new_plan)
        self.assertEqual(BillingHistory.objects.count(), 2)
        _bh = BillingHistory.objects.all()[0]
        invoice_num = 'RENT_CHNG_%s_%s' % (_bh.user.pk, _bh.pk)
        self.assertEqual(_bh.aim_response['invoice_number'], invoice_num)
        self.assertEqual(MemberRentalPlanHistory.objects.count(), 1)

    def test_downgrade(self):
        plan = RentalPlan.objects.get(slug="unlimited2")
        self.signup_plan(plan)
        new_plan = RentalPlan.objects.get(slug="unlimited1")
        mrp = MemberRentalPlan.objects.all()[0]
        change_plan(mrp, new_plan)
        self.assertEqual(BillingHistory.objects.count(), 1)
        self.assertEqual(mrp.rental_plan.slug, "unlimited2")
        _bh = BillingHistory.objects.all()[0]
        self.assertEqual(_bh.debit, plan.first_payment_amount)

        fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            call_command("rent", "recurring_billing")
        call_command("rent", "recurring_billing")
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.rental_plan.slug, "unlimited1")
        self.assertEqual(BillingHistory.objects.count(), 2)
        _bh = BillingHistory.objects.all()[0]
        self.assertEqual(_bh.debit, new_plan.thereafter_payments_amount)
