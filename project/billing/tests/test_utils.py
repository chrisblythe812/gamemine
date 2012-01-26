from django.test import TestCase

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.models import RentalPlan
from project.new_rent.utils import get_payment_invoice_num
from project.new_members.models import Profile
from project.members.models import BillingHistory
from project.billing.utils import take_money


class UtilsTests(TestCase, SignUpTestCase):
    def test_take_money(self):
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        profile = Profile.objects.all()[0]
        profile.bonus_store_credits = 5
        profile.store_credits = 5
        profile.save()

        def invoice_num_func(profile, billing_history):
            return get_payment_invoice_num(
                'rent', 'new', profile.user.pk, billing_history.pk)

        take_money(user_or_profile=profile, amount=10, reason='rent',
                    invoice_num_func=invoice_num_func, description='desc')
        bhi = BillingHistory.objects.all()[0]
        self.assertEqual(bhi.applied_credits, 5)
        self.assertEqual(bhi.debit, 5)
        self.assertEqual(bhi.aim_response['amount'], '5.0')
