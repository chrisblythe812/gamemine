from decimal import Decimal

from django.test import TestCase
from project.members.models import BillingHistory, Profile, TransactionType, TransactionStatus
from project.members.utils import build_aim_data
from project.utils import create_aim


class BillingHistoryTestCase(TestCase):
    def setUp(self):
        shipping_data = billing_data = {
            "first_name": u"Test",
            "last_name": u"User",
            "address1": u"1 Test St",
            "address2": u"",
            "city": u"Test City",
            "state": u"AK",
            "zip_code": u"12345",
        }

        billing_card_data = {
            "type": u"visa",
            "number": u"4111111111111111",
            "code": u"123",
            "exp_month": u"1",
            "exp_year": u"2018",
        }

        self.profile = Profile.objects.build_and_create(
            username="test_user",
            email="test@email.com",
            password="19891010",
            shipping_data=shipping_data,
            billing_data=billing_data,
            billing_card_data=billing_card_data,
        )

        aim_data = build_aim_data(
            shipping_data, billing_data, billing_card_data,
            invoice_num="123",
            description="Test Payment",
            email=self.profile.user.email,
            tax=Decimal("1")
        )

        aim = create_aim()
        aim_response = aim.authorize(Decimal("10"), **aim_data)

        self.billing_history = BillingHistory.objects.create(
            user=self.profile.user,
            payment_method=self.profile.get_billing_card_display(),
            description="Test Payment",
            debit=Decimal("10"),
            reason="test-reason",
            type=TransactionType.Unknown,
            card_data=self.profile.get_billing_card_data(),
            tax=Decimal("1"),
            status=TransactionStatus.Authorized,
            aim_transaction_id=aim_response.transaction_id,
            aim_response=aim_response._as_dict,
            message=aim_response.response_reason_text
        )

    def test_capture(self):
        capture_result = self.billing_history.capture()
        first_payment, second_payment = BillingHistory.objects.order_by("pk")

        self.assertEqual(BillingHistory.objects.count(), 2)
        self.assertEqual(first_payment.status, TransactionStatus.Authorized)
        self.assertEqual(second_payment.status, TransactionStatus.Passed)
