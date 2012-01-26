from django.test import TestCase

from project.new_members.tests.regressiontests.signup import SignUpTestCase
from project.new_members.models import Profile


class SignUpTests(TestCase, SignUpTestCase):
    def test_signup(self):
        self.signup()
        self.login()
        self.assertEqual(Profile.objects.count(), 1)

    def test_pixels(self):
        self.signup(url_suffix="?cid=123")
        self.login()
        self.assertEqual(Profile.objects.count(), 1)
        profile = Profile.objects.all()[0]
        self.assertEqual(profile.campaign_cid, "123")
