# Deprecated
from decimal import Decimal
import datetime

from django.test import TestCase

from nose.plugins.skip import SkipTest

from django_snippets.utils.datetime.date_utils import inc_date
from project.new_rent.models import MemberRentalPlan, RentalPlan
from project.members.models import BillingCard


class BuildAndCreateTestCase(TestCase):
    def setUp(self):
        raise SkipTest

    def test_build_and_create(self):
        shipping_data = {
            "first_name": u"Test",
            "last_name": u"User",
            "address1": u"1 Test St",
            "address2": u"",
            "city": u"Test City",
            "state": u"AK",
            "zip_code": u"12345",
        }

        billing_data = {
            "first_name": u"Test",
            "last_name": u"User",
            "address1": u"1 Test St",
            "address2": u"",
            "city": u"Test City",
            "state": u"AK",
            "zip_code": u"12345",
            # "country": "USA",
        }

        billing_card_data = {
            "type": u"visa",
            "number": u"4111111111111111",
            "code": u"123",
            "exp_month": u"1",
            "exp_year": u"2018",
        }

        kwargs = {
            "rental_plan": RentalPlan.objects.all()[0],
            "email": u"test@email.com",
            "username": u"test_user",
            "password": u"19891010",
            "how_did_you_hear": 1,
            "phone": u"(123) 123-1234",
            "customer_ip": "127.0.0.1",
            "campaign_id": "123",
            "sid": "321",
            "affiliate": "456",
        }
        mrp = MemberRentalPlan.objects.build_and_create(
            shipping_data=shipping_data,
            billing_data=billing_data,
            billing_card_data=billing_card_data,
            **kwargs
        )
        self.assertTrue(mrp)
        self.assertTrue(mrp.user)
        self.assertEqual(mrp.user, BillingCard.objects.all()[0].user)
        self.assertTrue(BillingCard.objects.all()[0].data)
        self.assertEqual(mrp.plan, RentalPlan.PlanA)
        self.assertEqual(mrp.start_date.date(), datetime.date.today())
        self.assertEqual(mrp.expiration_date, None)
        self.assertEqual(mrp.next_payment_date, inc_date(datetime.date.today(), "1m"))
        self.assertEqual(mrp.next_payment_amount, Decimal("8.99"))
        self.assertTrue(mrp.first_payment)
        self.assertTrue(mrp.user.get_profile().get_billing_card_data())
        self.assertEqual(mrp.first_payment.user, mrp.user)
