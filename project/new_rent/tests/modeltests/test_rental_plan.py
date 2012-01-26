import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from django_snippets.utils.datetime import inc_date
from project.new_rent.models import RentalPlan
from project.new_members.models import Profile
from project.members.models import BillingCard


class RentalPlanTestCase(TestCase):
    def test_rental_plan(self):
        self.assertTrue(RentalPlan.objects.get(pk=0))
        self.assertEqual(len(RentalPlan.objects.all_active()), 4)

    def test_get_fp_description(self):
        rental_plan = RentalPlan.objects.get(pk=0)
        print rental_plan.get_first_payment_description(123)

    def test_get_next_payment(self):
        #
        # Limited 1
        #
        rental_plan = RentalPlan.objects.all_active()[0]

        # First Payment
        date, amount, type_ = rental_plan.get_next_payment()
        self.assertEqual(date, datetime.date.today())
        self.assertEqual(amount, rental_plan.first_payment_amount)
        self.assertEqual(type_, "AUTH_CAPTURE")

        # Thereafter Payment
        date, amount, type_ = rental_plan.get_next_payment(datetime.date.today())
        self.assertEqual(date, inc_date(datetime.date.today(), "1m"))
        self.assertEqual(amount, rental_plan.thereafter_payments_amount)
        self.assertEqual(type_, "AUTH_CAPTURE")
        # ---

        #
        # Free Trial
        #
        rental_plan = RentalPlan.objects.get(slug="free_trial")

        # First Payment
        date, amount, type_ = rental_plan.get_next_payment()
        self.assertEqual(date, datetime.date.today())
        self.assertEqual(amount, rental_plan.first_payment_amount)
        self.assertEqual(type_, "AUTH_ONLY")

        # Thereafter Payment
        # Actually this doesn't matter because there will be no
        # thereafter payments for Free Trial (we have set
        # scheduled_plan to PlanB)
        date, amount, type_ = rental_plan.get_next_payment(datetime.date.today())
        self.assertEqual(date, inc_date(datetime.date.today(), "10d"))
        self.assertEqual(amount, None)
        self.assertEqual(type_, "AUTH_CAPTURE")
        # ---

    def test_make_first_payment(self):
        test_user = User.objects.create(
            username="test_user",
            email="test@email.com",
            first_name=u"Test",
            last_name=u"User"
        )
        test_card = BillingCard.objects.create(
            user=test_user,
            first_name=u"Test",
            last_name=u"User",
            address1=u"1 Test St",
            city=u"Test City",
            state=u"AK",
            zip=u"12345",
            data={
                "type": u"visa",
                "number": u"4111111111111111",
                "code": u"123",
                "exp_month": u"1",
                "exp_year": u"2018",
            }
        )
        test_profile = Profile.objects.create(
            user=test_user,
            shipping_address1=u"1 Test St",
            shipping_city=u"Test City",
            shipping_state=u"AK",
            shipping_zip=u"12345",
        )
        rental_plan = RentalPlan.objects.all_active()[0]

        rental_plan.make_first_payment(
            test_user,
            test_profile,
            test_card,
            customer_ip="127.0.0.1"
        )

    def test_first_payment_description(self):
        def format_date(date_):
            from django.template.defaultfilters import date
            return date(date_, 'M j, Y')

        rental_plan = RentalPlan.objects.all_active()[0]
        _inum, desc = rental_plan.get_first_payment_description("123")
        next_payment_date = format_date(inc_date(datetime.date.today(), "1m"))
        self.assertTrue(next_payment_date in desc)
