import datetime

from django.core.management import call_command
from django.test import TestCase

from fudge import Fake, patched_context

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.tests.regressiontests.changeplan import ChangePlanTestCase
from project.new_rent.models import MemberRentalPlan, RentalPlan
from project.members.models import BillingHistory, Refund


class RentChangePlanTestCase(TestCase, SignUpTestCase, ChangePlanTestCase):
    def test_change_plan_1_2(self):
        unlimited_1 = RentalPlan.objects.get(slug="unlimited1")
        unlimited_2 = RentalPlan.objects.get(slug="unlimited2")
        self.signup_plan(unlimited_1)
        self.change_plan(unlimited_2)

        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.rental_plan, unlimited_2)
        self.assertEqual(BillingHistory.objects.count(), 2)

    def test_change_plan_old_limited_2(self):
        unlimited_1 = RentalPlan.objects.get(slug="unlimited1")
        old_limited = RentalPlan.objects.get(slug="old_limited")
        unlimited_2 = RentalPlan.objects.get(slug="unlimited2")
        self.signup_plan(unlimited_1)
        mrp = MemberRentalPlan.objects.all()[0]
        mrp.plan = old_limited.pk
        mrp.next_payment_amount = old_limited.thereafter_payments_amount
        mrp.save()
        self.change_plan(unlimited_2)

        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.rental_plan, unlimited_2)
        self.assertEqual(BillingHistory.objects.count(), 2)

        # fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        # with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
        call_command("rent", "recurring_billing")
        call_command("rent", "delinquent_billing")
        call_command("rent", "purge")
        call_command("rent", "process_matrix")
        call_command("rent", "process_cancellations")
        call_command("rent", "move_orders")
        self.assertEqual(BillingHistory.objects.count(), 2)

    def test_change_plan_2_1(self):
        unlimited_1 = RentalPlan.objects.get(slug="unlimited1")
        unlimited_2 = RentalPlan.objects.get(slug="unlimited2")
        self.signup_plan(unlimited_2)
        self.change_plan(unlimited_1)

        mrp = MemberRentalPlan.objects.all()[0]
        # Plan not changed yet
        self.assertEqual(mrp.rental_plan, unlimited_2)
        self.assertEqual(BillingHistory.objects.count(), 1)
        self.assertEqual(Refund.objects.count(), 0)

        mrp.next_payment_date = datetime.date.today()
        mrp.save()
        # Now changed
        call_command("rent", "recurring_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.rental_plan, unlimited_1)
        # Because it's downgrade not billing user
        self.assertEqual(BillingHistory.objects.count(), 1)
        # No refund though
        self.assertEqual(Refund.objects.count(), 0)

    def test_change_plan_prepaid6_unlimited1(self):
        unlimited_1 = RentalPlan.objects.get(slug="unlimited1")
        prepaid_6 = RentalPlan.objects.get(slug="unlimited_prepaid6")
        self.signup_plan(unlimited_1)
        mrp = MemberRentalPlan.objects.all()[0]
        mrp.rental_plan = prepaid_6
        mrp.next_payment_date = None
        mrp.next_payment_amount = None
        mrp.expiration_date = datetime.date(2012, 6, 17)
        mrp.save()
        self.change_plan(unlimited_1)

        mrp = MemberRentalPlan.objects.all()[0]
        # Can't change prepaid plan
        self.assertEqual(mrp.rental_plan, prepaid_6)

    def test_change_plan_free_trial_unlimited1(self):
        free_trial = RentalPlan.objects.get(slug="free_trial")
        unlimited_1 = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(free_trial)
        self.change_plan(unlimited_1)

        mrp = MemberRentalPlan.objects.all()[0]
        # Can't change free_trial plan
        self.assertEqual(mrp.rental_plan, free_trial)
