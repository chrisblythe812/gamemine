from django.core.urlresolvers import reverse


class ChangePlanTestCase(object):
    def change_plan(self, rental_plan):
        plan = str(rental_plan.pk)

        response = self.client.get(reverse("new_rent:change_plan"))
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "change_rent_plan_wizard-current_step": u"0",
            "0-rental_plan": plan
        }
        response = self.client.post(reverse("new_rent:change_plan"), data)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            reverse("new_rent:change_plan"),
            {'change_rent_plan_wizard-current_step': '1'},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("new_rent:change_plan"))
        self.failUnlessEqual(response.status_code, 200)
