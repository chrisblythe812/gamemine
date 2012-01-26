import datetime

from django.core.management import call_command
from django.test import TestCase

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.tests.regressiontests.changeplan import ChangePlanTestCase
from project.new_rent.models import MemberRentalPlan, RentalPlan
from project.members.models import BillingHistory


class RentChangePlanTestCase(TestCase, SignUpTestCase, ChangePlanTestCase):
    def test_free_trial(self):
        free_trial = RentalPlan.objects.get(slug="free_trial")
        unlimited_2 = RentalPlan.objects.get(slug="unlimited2")
        self.signup_plan(free_trial)

        mrp = MemberRentalPlan.objects.all()[0]

        mrp.next_payment_date = datetime.date.today()
        mrp.save()
        call_command("rent", "recurring_billing")
        call_command("rent", "recurring_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.rental_plan, unlimited_2)

        bh1, bh2 = BillingHistory.objects.all()
        self.assertEqual(bh1.aim_transaction_id, bh2.aim_transaction_id)
