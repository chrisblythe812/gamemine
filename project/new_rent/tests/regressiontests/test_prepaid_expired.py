import datetime

from django.test import TestCase
from django.core.management import call_command
from fudge import Fake, patched_context

from project.rent.models import MemberRentalPlan
from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.models import RentalPlan


class PrepaidExpiredTestCase(TestCase, SignUpTestCase):
    def test_prepaid_expired(self):
        # Member signed up for rental plan and have been billed first
        # time
        plan = RentalPlan.objects.get(slug="unlimited1")
        with patched_context(
            RentalPlan.objects,
            "available_for_signup",
            Fake().is_callable().calls(lambda request: RentalPlan.objects.all())):
            self.signup_plan(plan)  # Monthly 1 Game Plan
        mrp = MemberRentalPlan.objects.all()[0]

        # Setting plan expiration date to yesterday
        mrp.expiration_date = datetime.date.today() - datetime.timedelta(1)
        mrp.save()

        call_command("rent", "recurring_billing")
        call_command("rent", "purge")
        call_command("rent", "process_cancellations")

        # Expired plan cancelled and deleted
        self.assertEqual(MemberRentalPlan.objects.count(), 0)
