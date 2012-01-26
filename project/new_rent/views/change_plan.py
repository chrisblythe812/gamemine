from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.utils.decorators import classonlymethod
from project.utils.wizard.views import SessionWizardView

from django_snippets.views import JsonResponse
from deferred_messages import add_deferred_message

from project.new_members.forms import (
    RentalPlanForm, ConfirmChangeRentPlanForm,
    BillingForm
)
from project.new_rent.models import RentalPlan, MemberRentalPlan
from project.new_rent.utils import get_charge_for_the_rest_of_month, change_plan
from project.members.models import BillingCard
from project.billing.utils import PaymentError


class ChangeRentPlanWizard(SessionWizardView):
    form_list = [RentalPlanForm, ConfirmChangeRentPlanForm]

    @classonlymethod
    def as_view(cls, *args, **kwargs):
        kwargs.update({
                "form_list": cls.form_list,
                "initial_dict": cls.initial_dict,
                "instance_dict": cls.instance_dict,
                "condition_dict": cls.condition_dict,
        })
        return super(ChangeRentPlanWizard, cls).as_view(*args, **kwargs)

    def render(self, form=None, **kwargs):
        # Handling redirects here

        # If this is ajax request and anonymous or user without rental
        # plan, redirecting him
        # to ajax dialog rental plan signup, we need this for compatibility
        if (self.request.is_ajax() and
            (not self.request.user.is_authenticated() or
             self.request.user.is_authenticated() and
             not self.request.user.profile.is_rental_active())):
            return redirect("new_rent:sign_up")
        # If anonymous user and normal request redirecting to login page
        if not self.request.user.is_authenticated():
            return redirect_to_login(reverse("new_rent:change_plan"))
        # If registered user without rental plan redirecting to index
        if not self.request.user.get_profile().member_rental_plan:
            return redirect("index")

        return super(ChangeRentPlanWizard, self).render(form, **kwargs)

    def get_form_kwargs(self, step=None):
        return {
            "request": self.request,
        }

    def get_context_data(self, form, **kwargs):
        context = super(ChangeRentPlanWizard, self).get_context_data(form, **kwargs)
        _context = getattr(self, "get_context_data_%s" % self.steps.current)(form, **kwargs)
        context.update(_context)
        return context

    def get_context_data_0(self, form, **kwargs):
        return {
                "limited_plans": RentalPlan.objects.available_for_change_limited(self.request),
                "unlimited_plans": RentalPlan.objects.available_for_change_unlimited(self.request),
        }

    def get_context_data_1(self, form, **kwargs):
        old_member_rental_plan = self.request.user.get_profile().member_rental_plan
        new_rental_plan = self.get_all_cleaned_data()['rental_plan']
        charge_for_the_rest_of_month = will_be_billed = \
                get_charge_for_the_rest_of_month(
                    old_member_rental_plan, new_rental_plan
                )
        payment_card = BillingCard.objects.get(user=self.request.user).display_number
        is_upgrade = old_member_rental_plan.rental_plan.is_upgrade(new_rental_plan)
        if is_upgrade:
            plan_starts = "now"
        else:
            plan_starts = old_member_rental_plan.next_payment_date
        return {
            "new_rental_plan": new_rental_plan,
            "charge_for_the_rest_of_month": charge_for_the_rest_of_month,
            "plan_starts": plan_starts,
            "will_be_billed": will_be_billed,
            "payment_card": payment_card,
            "is_upgrade": is_upgrade,
        }

    def get_template_names(self):
        step = self.steps.current

        template_name = {
            "0": "new_rent/change_plan.html",
            "1": "new_rent/change_plan_partials/step1.html",
        }[step]
        return [template_name]

    def render_payment_failure(self, billing_form, message):
        billing_form._errors = {"__all__": [message]}
        res = self.render(billing_form)
        return res

    def render_done(self, form, **kwargs):
        try:
            return super(ChangeRentPlanWizard, self).render_done(form, **kwargs)
        # The only error we could expect is PaymentError, if so going
        # one step back and displaying error message
        except PaymentError, exc:
            billing_form = self.get_form(step="1",
                data=self.storage.get_step_data("1"),
                files=self.storage.get_step_files("1"))
            return self.render_payment_failure(billing_form, exc.message)

    def done(self, form_list, **kwargs):
        old_member_rental_plan = self.request.user.get_profile().member_rental_plan
        new_rental_plan = self.get_all_cleaned_data()['rental_plan']
        change_plan(old_member_rental_plan, new_rental_plan)
        is_upgrade = old_member_rental_plan.rental_plan.is_upgrade(new_rental_plan)
        if is_upgrade:
            plan_starts = "now"
            add_deferred_message(
                self.request,
                messages.INFO,
                "You have successfully changed your plan to %s" %
                    new_rental_plan.description2
            )
        else:
            plan_starts = old_member_rental_plan.next_payment_date
            add_deferred_message(
                self.request,
                messages.INFO,
                "Your plan will be changed to %s on %s" %
                    (new_rental_plan.description2, plan_starts)
            )
        return JsonResponse({'redirect_to': reverse("new_rent:change_plan")})
