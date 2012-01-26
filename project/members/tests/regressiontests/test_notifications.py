from django.test import TestCase
from django.core import mail
from django.conf import settings

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.rent.models import RentalPlan, MemberRentalPlan


class NotificationsTestCase(TestCase, SignUpTestCase):
    def test_notifications(self):
        # settings.EMAIL_BACKEND = "project.utils.mail.backends.htmlfiles.EmailBackend"
        # settings.EMAIL_FILE_PATH = "/Users/t0ster/Downloads"
        settings.EMAIL_STATIC_URL = "http://localhost:8000/m/"

        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        MemberRentalPlan.objects.all()[0].send_account_is_reactivated()
        MemberRentalPlan.objects.all()[0].send_personal_game_received()
        self.assertEqual(len(mail.outbox), 3)
