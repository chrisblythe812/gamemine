from django.test import TestCase

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.tests.mixins.check_call import CheckCallMixin
from project.new_rent.models import MemberRentalPlan, RentalPlan
from authorizenet.aim import AIM


class MoneyTestCase(TestCase, SignUpTestCase, CheckCallMixin):
    def setUp(self):
        self._aim_capture = AIM.capture
        self._aim_authorize = AIM.authorize

    def tearDown(self):
        AIM.capture = self._aim_capture
        AIM.authorize = self._aim_authorize

    def test_take_money(self):
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        mrp = MemberRentalPlan.objects.all()[0]

        amount = "10.0"
        tax_amount = "0"

        AIM.capture = self.check_call_decorator(
            lambda args, kwargs: args[1] == "10.00" and kwargs["invoice_num"] == "RENT_NEW_123"
        )(AIM.capture)

        invoice_num, description = mrp.get_payment_description(
            new_or_reccuring=True, trans_id=123, reccuring=False)

        success, aim_response, applied_credits, applied_amount = mrp.take_money(
            amount, tax_amount, invoice_num, description, aim_data={})

        self.assertCheckCall()
        self.assertEqual("10.00", aim_response.amount)
        self.assertEqual("10.0", applied_amount)
        self.assertEqual("AUTH_CAPTURE", aim_response.transaction_type)
