import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from fudge import Fake, patched_context

from project.members.models import BillingHistory, TransactionStatus
from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.models import RentalPlan
from project.new_rent.models import MemberRentalPlan, RentalPlanStatus


class BillingTestCase(TestCase, SignUpTestCase):
    def tearDown(self):
        settings.AUTH_NET_CONF["test_response_code"] = 1  # All OK

    def test_unlimited_1_plan(self):
        # Member signed up for rental plan and have been billed first
        # time
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        mrp = MemberRentalPlan.objects.all()[0]

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(BillingHistory.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Gamemine - Thanks for Joining Gamemine!")
        self.assertEqual(mrp.get_status_display(), "Active")

        # Calling ``rent recurring_billing`` command, member should be
        # billed
        fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            call_command("rent", "recurring_billing")
        self.assertEqual(BillingHistory.objects.count(), 2)

    def test_free_trial(self):
        # Member signed up for rental plan and have been billed first
        # time
        free_trial = RentalPlan.objects.get(slug="free_trial")
        unlimited2 = RentalPlan.objects.get(slug="unlimited2")
        self.signup_plan(free_trial)
        # ``MemberRentalPlan.authorize_money`` should be called
        mrp = MemberRentalPlan.objects.all()[0]
        billing_history = BillingHistory.objects.all()[0]

        self.assertEqual(billing_history.aim_response["transaction_type"], u"AUTH_ONLY")
        self.assertEqual(billing_history.status, TransactionStatus.Authorized)

        fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            # First `recurring_billing` changes plan to unlimited 2
            call_command("rent", "recurring_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.rental_plan, unlimited2)

        # Second `recurring_billing` bills user
        call_command("rent", "recurring_billing")
        billing_history = BillingHistory.objects.order_by("pk")[1]

        self.assertEqual(BillingHistory.objects.count(), 2)
        self.assertEqual(billing_history.status, TransactionStatus.Passed)
        self.assertEqual(billing_history.aim_response["transaction_type"], u"PRIOR_AUTH_CAPTURE")

        # Third `recurring_billing` -- nothing
        call_command("rent", "recurring_billing")
        self.assertEqual(BillingHistory.objects.count(), 2)

        # `recurring_billing` again
        mrp = MemberRentalPlan.objects.all()[0]
        fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            call_command("rent", "recurring_billing")
        billing_history = BillingHistory.objects.order_by("pk")[2]

        self.assertEqual(BillingHistory.objects.count(), 3)
        self.assertEqual(billing_history.aim_response["transaction_type"], u"AUTH_CAPTURE")

    def test_free_trial_discard(self):
        # Trying to bill member with insufficient funds on CC
        free_trial = RentalPlan.objects.get(slug="free_trial")
        unlimited2 = RentalPlan.objects.get(slug="unlimited2")
        self.signup_plan(free_trial)  # Free Trial

        settings.AUTH_NET_CONF["test_response_code"] = 2  # Insufficient funds

        mrp = MemberRentalPlan.objects.all()[0]

        fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            # Changes plan from Free Trial to Unlimited Monthly 2
            call_command("rent", "recurring_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(BillingHistory.objects.count(), 1)
        self.assertEqual(mrp.status, RentalPlanStatus.Active)
        self.assertEqual(mrp.rental_plan, unlimited2)

        fake_now = datetime.datetime.combine(mrp.next_payment_date, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            # Captures money ("PRIOR_AUTH_CAPTURE")
            call_command("rent", "recurring_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(BillingHistory.objects.count(), 2)
        self.assertEqual(mrp.status, RentalPlanStatus.Delinquent)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Oops, we have a billing problem!")

        settings.AUTH_NET_CONF["test_response_code"] = 1

        fake_now = datetime.datetime.combine(mrp.delinquent_next_check, datetime.time())
        with patched_context(datetime.datetime, "now", Fake().is_callable().returns(fake_now)):
            call_command("rent", "delinquent_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        billing_history = BillingHistory.objects.order_by("pk")[2]
        self.assertEqual(BillingHistory.objects.count(), 3)
        self.assertEqual(mrp.status, RentalPlanStatus.Active)
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[2].subject, "Gamemine - Billing Charge Approved")
        self.assertEqual(billing_history.aim_response["transaction_type"], u"AUTH_CAPTURE")
