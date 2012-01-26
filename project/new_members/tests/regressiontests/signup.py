import re

from django.core import mail
from django.core.urlresolvers import reverse


class SignUpTestCase(object):
    def signup(self, url_suffix=""):
        response = self.client.get(reverse("members:create_account") + url_suffix)
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "username": u"t0ster_user",
            "confirm_password": u"19891010",
            "first_name": u"Roman",
            "last_name": u"Dolgiy",
            "agree_of_terms": u"on",
            "password": u"19891010",
            "phone_number": u"(123) 123-1234",
            "email": u"tosters@gmail.com"
        }
        response = self.client.post(reverse("members:create_account"), data)
        self.assertRedirects(response, reverse("members:create_account_complete"))

        response = self.client.get(reverse("members:create_account_complete"))
        self.assertContains(response, "Verify your email address", status_code=200)

        email = mail.outbox[0].body
        verify_url = re.search(r'http://localhost:8000(/Member-Home/Confirm(.+))"', email).groups()[0]
        response = self.client.get(verify_url)
        self.assertContains(response, "Email address has been verified", status_code=200)

    def login(self):
        response = self.client.get(reverse("members:login"))
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "password": u"19891010",
            "remember": u"on",
            "email": u"tosters@gmail.com",
        }
        response = self.client.post(reverse("members:login"), data)
