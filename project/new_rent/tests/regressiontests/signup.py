from django.core.urlresolvers import reverse

from project.tds.utils import FREE_TRIAL_CIDS
from project.new_rent.models import RentalPlan


class SignUpTestCase(object):
    def signup_plan_0(self, plan, no_asserts=False, use_melissa=False, qstring=""):
        free_trial_cid = FREE_TRIAL_CIDS[0]
        free_trial_plan = RentalPlan.objects.get(slug="free_trial")
        if not qstring:
            qstring = plan == free_trial_plan and ("?cid=%s" % free_trial_cid) or ""
        plan_pk = str(plan.pk)

        self.last_response = self.client.get(
            reverse("new_rent:sign_up") + qstring,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.failUnlessEqual(self.last_response.status_code, 200)

        data = {
            "non_member_rent_sign_up_wizard-current_step": u"0",
            "0-rental_plan": plan_pk,
        }
        self.last_response = self.client.post(reverse("new_rent:sign_up"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        if not no_asserts:
            self.assertContains(self.last_response, "1-email", count=None, status_code=200, msg_prefix='')

    def signup_plan_1(self, plan, no_asserts=False, use_melissa=False):
        data = {
            "1-username": u"t0ster_user",
            "1-last_name": u"Dolgiy",
            "1-email": u"tosters@gmail.com",
            "1-first_name": u"Roman",
            "1-password": u"19891010",
            "1-confirm_password": u"19891010",
            "1-phone_number": u"(123) 123-1234",
            "1-city": u"Kiev",
            "1-zip_code": u"12345",
            "non_member_rent_sign_up_wizard-current_step": u"1",
            "1-state": u"FL",
            "1-how_did_you_hear": u"1",
            "1-address1": u"13 Test St",
            "1-address2": u""
        }
        self.last_response = self.client.post(reverse("new_rent:sign_up"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        if use_melissa:
            data = {
            "1-username": u"t0ster_user",
            "1-last_name": u"Dolgiy",
            "1-email": u"tosters@gmail.com",
            "1-first_name": u"Roman",
            "1-password": u"19891010",
            "1-confirm_password": u"19891010",
            "1-phone_number": u"(123) 123-1234",
            "1-city": u"New New York",
            "1-zip_code": u"12345",
            "non_member_rent_sign_up_wizard-current_step": u"1",
            "1-state": u"FL",
            "1-how_did_you_hear": u"1",
            "1-address1": u"13 Test St",
            "1-address2": u""
            }
            self.last_response = self.client.post(reverse("new_rent:sign_up"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        if not no_asserts:
            self.assertContains(self.last_response, "Credit Card", count=None, status_code=200, msg_prefix='')

    def signup_plan_2(self, plan, no_asserts=False, use_melissa=False):
        data = {
            "2-city": u"New York",
            "2-zip_code": u"12345",
            "2-exp_month": u"1",
            "2-exp_year": u"2012",
            "2-number": u"4111111111111111",
            "2-code": u"123",
            "non_member_rent_sign_up_wizard-current_step": u"2",
            "2-state": u"FL",
            "2-first_name": u"Roman",
            "2-address1": u"13 Test St",
            "2-type": u"visa",
            "2-address2": u"",
            "2-last_name": u"Dolgiy"
        }
        self.last_response = self.client.post(reverse("new_rent:sign_up"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        if use_melissa:
            data = {
            "2-city": u"New New York",
            "2-zip_code": u"12345",
            "2-exp_month": u"1",
            "2-exp_year": u"2012",
            "2-number": u"4111111111111111",
            "2-code": u"123",
            "non_member_rent_sign_up_wizard-current_step": u"2",
            "2-state": u"FL",
            "2-first_name": u"Roman",
            "2-address1": u"13 Test St",
            "2-type": u"visa",
            "2-address2": u"",
            "2-last_name": u"Dolgiy"
            }
            self.last_response = self.client.post(reverse("new_rent:sign_up"), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        if not no_asserts:
            self.assertContains(self.last_response, "redirect_to", count=None, status_code=200, msg_prefix='')
            self.last_response = self.client.get(reverse("rent:confirmation"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.failUnlessEqual(self.last_response.status_code, 200)

    def signup_plan(self, plan, use_melissa=False, qstring=""):
        self.signup_plan_0(plan, use_melissa=use_melissa, qstring=qstring)
        self.signup_plan_1(plan, use_melissa=use_melissa)
        self.signup_plan_2(plan, use_melissa=use_melissa)

    def member_signup_plan(self, plan):
        plan_pk = str(plan.pk)

        response = self.client.get(
            reverse("new_rent:sign_up"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "member_rent_sign_up_wizard-current_step": u"0",
            "0-rental_plan": plan_pk
        }
        response = self.client.post(reverse("new_rent:sign_up"),
                        data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertContains(response, "1-last_name", count=None, status_code=200, msg_prefix='')

        data = {
            "1-last_name": u"Dolgiy",
            "1-first_name": u"Roman",
            "1-city": u"Kiev",
            "member_rent_sign_up_wizard-current_step": u"1",
            "1-state": u"AK",
            "1-zip_code": u"12345",
            "1-address1": u"13 Test St",
            "1-address2": u""
        }
        response = self.client.post(reverse("new_rent:sign_up"), data,
                        HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertContains(response, "Credit Card", count=None, status_code=200, msg_prefix='')

        data = {
            "2-city": u"Kiev",
            "2-zip_code": u"12345",
            "2-exp_month": u"1",
            "2-exp_year": u"2012",
            "2-number": u"4111111111111111",
            "2-code": u"123",
            "member_rent_sign_up_wizard-current_step": u"2",
            "2-state": u"AK",
            "2-first_name": u"Roman",
            "2-address1": u"13 Test St",
            "2-type": u"visa",
            "2-address2": u"",
            "2-last_name": u"Dolgiy"
        }
        response = self.client.post(reverse("new_rent:sign_up"),
                        data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.failUnlessEqual(response.status_code, 200)
