import datetime
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.contrib.auth.models import User
from nose.plugins.skip import SkipTest

from django_snippets.utils.datetime import inc_date
from project.new_rent.tests.regressiontests.signup import SignUpTestCase as RentSignUpTestCase
from project.new_members.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.models import MemberRentalPlan, RentalPlan
from project.members.models import BillingHistory, BillingCard
from project.new_members.models import Profile


class RentSignUpTests(TestCase, SignUpTestCase, RentSignUpTestCase):
    def tearDown(self):
        settings.AUTH_NET_CONF["test_response_code"] = 1  # All OK
        import melissadata.melissa
        melissadata.melissa.TEST_MODE = False
        settings.MELISSA_CONFIG['use_melissa'] = False

    def test_signup_plan_limited(self):
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(MemberRentalPlan.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertTrue(Profile.objects.all()[0].shipping_state)
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.plan, plan.pk)
        self.assertEqual(mrp.start_date, datetime.date.today())
        self.assertEqual(mrp.expiration_date, None)
        self.assertEqual(mrp.next_payment_date, inc_date(datetime.date.today(), "1m"))
        self.assertEqual(mrp.next_payment_amount, mrp.rental_plan.thereafter_payments_amount)
        self.assertTrue(mrp.first_payment)

        card = BillingCard.objects.all()[0]
        self.assertTrue(card.data.get("exp_year"))
        self.assertTrue(card.type)

    def test_signup_plan_free_trial(self):
        plan = RentalPlan.objects.get(slug="free_trial")  # Monthly 1 Game Plan
        self.signup_plan(plan)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(MemberRentalPlan.objects.count(), 1)
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.plan, plan.pk)
        self.assertEqual(mrp.start_date, datetime.date.today())
        self.assertEqual(mrp.expiration_date, None)
        self.assertEqual(mrp.next_payment_date, inc_date(datetime.date.today(), "10d"))
        self.assertEqual(mrp.next_payment_amount, None)
        self.assertTrue(mrp.first_payment)

    def test_signup_deprecated_plan(self):
        raise SkipTest
        plan = RentalPlan.objects.get(slug="unlimited_prepaid3")  # 3 Months 2 Game Plan
        response = self.client.get(
            reverse("new_rent:sign_up"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            reverse("new_rent:sign_up"),
            {"non_member_rent_sign_up_wizard-current_step": u"0",
             "0-plan": plan.pk},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertNotContains(response, "1-email", status_code=200, msg_prefix='')

    def test_store_credits(self):
        plan = RentalPlan.objects.get(slug="unlimited1")  # Monthly 1 Game Plan
        self.signup_plan(plan)
        mrp = MemberRentalPlan.objects.all()[0]
        profile = mrp.user.get_profile()
        profile.store_credits = Decimal("50")
        profile.save()
        mrp.next_payment_date = datetime.date.today()
        mrp.save()

        call_command("rent", "recurring_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        profile = mrp.user.get_profile()
        last_payment = BillingHistory.objects.all()[0]
        self.assertNotEqual(mrp.next_payment_date, datetime.date.today())
        self.assertEqual(profile.store_credits, Decimal("36.05"))
        self.assertFalse(last_payment.aim_response)
        self.assertEqual(last_payment.applied_credits, Decimal("13.95"))
        self.assertEqual(last_payment.debit, Decimal("0"))
        self.assertEqual(last_payment.payment_method, u"Store Credits")

        call_command("rent", "recurring_billing")

        mrp = MemberRentalPlan.objects.all()[0]
        profile = mrp.user.get_profile()
        self.assertEqual(profile.store_credits, Decimal("36.05"))

    def test_signup_declined_cc(self):
        settings.AUTH_NET_CONF["test_response_code"] = 2  # Insufficient funds
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan_0(plan)
        self.signup_plan_1(plan)
        self.signup_plan_2(plan, no_asserts=True)
        self.assertContains(self.last_response, "This transaction has been declined", status_code=200)

    def test_member_signup(self):
        self.signup()
        self.login()
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.member_signup_plan(plan)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(MemberRentalPlan.objects.count(), 1)

    def test_signup_melissa(self):
        import melissadata.melissa
        melissadata.melissa.TEST_MODE = True
        settings.MELISSA_CONFIG['use_melissa'] = True
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan, use_melissa=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(MemberRentalPlan.objects.count(), 1)

    def test_pixels(self):
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan, qstring="?cid=123&PID=lMh2Xiq9xN0-eLDLEZmz_7RawtM3jsxCPg")
        profile = Profile.objects.all()[0]
        self.assertEqual(profile.campaign_cid, "123")
        self.assertEqual(profile.sid, "lMh2Xiq9xN0-eLDLEZmz_7RawtM3jsxCPg")
