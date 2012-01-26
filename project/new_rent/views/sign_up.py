from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.utils.decorators import classonlymethod
from django.contrib.auth import authenticate, login

from project.utils.wizard.views import SessionWizardView

from django_snippets.views.json_response import JsonResponse

from project.utils import get_melissa, create_aim
from project.new_members.forms import (
    RentalPlanForm, ProfileAndShippingCreationForm,
    ProfileAndShippingChangeForm, BillingForm
)
from project.new_rent.models import RentalPlan
from project.members.models import BillingCard
from project.new_rent.utils import rent_signup_for_member, rent_signup_for_new_user
from project.billing.utils import PaymentError


def show_rental_plan_form_condition(wizard):
    # If we have rental_plan defined in url, just skipping 0 step
    if wizard.storage.data.get("skip_step_0"):
        return False
    rental_plan_slug = wizard.kwargs.get("rental_plan_slug")
    if rental_plan_slug:
        rental_plan = RentalPlan.objects.get(slug=rental_plan_slug)
        form = wizard.get_form("0", {"0-rental_plan": rental_plan.pk})
        if form.is_valid():
            wizard.storage.set_step_data("0", wizard.process_step(form))
            wizard.storage.data["skip_step_0"] = True
            return False
    return True


class BaseRentSignUpWizard(SessionWizardView):
    condition_dict = {"0": show_rental_plan_form_condition}

    @classonlymethod
    def as_view(cls, *args, **kwargs):
        kwargs.update({
                "form_list": cls.form_list,
                "initial_dict": cls.initial_dict,
                "instance_dict": cls.instance_dict,
                "condition_dict": cls.condition_dict,
        })
        return super(BaseRentSignUpWizard, cls).as_view(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # Allowing only ajax requests
        if not request.is_ajax():
            return redirect("index")
        return super(BaseRentSignUpWizard, self).dispatch(request, *args, **kwargs)

    def get_form(self, step=None, data=None, files=None):
        """
        Constructs the form for a given `step`. If no `step` is defined, the
        current step will be determined automatically.

        The form will be initialized using the `data` argument to prefill the
        new form. If needed, instance or queryset (for `ModelForm` or
        `ModelFormSet`) will be added too.
        """
        if step is None:
            step = self.steps.current
        # prepare the kwargs for the form instance.
        kwargs = self.get_form_kwargs(step)
        kwargs.update({
            'data': data,
            'files': files,
            'prefix': self.get_form_prefix(step, self.form_list[step]),
            'initial': self.get_form_initial(step),
        })
        if step in ["1", "2"]:
            kwargs.update({'instance': self.get_form_instance(step)})
        return self.form_list[step](**kwargs)

    def post(self, *args, **kwargs):
        # Handling back button
        backward = self.request.POST.get('__backward', None)
        if backward:
            self.storage.current_step = self.get_prev_step()
            form = self.get_form(
                data=self.storage.get_step_data(self.steps.current),
                files=self.storage.get_step_files(self.steps.current))
            return self.render(form)

        return super(BaseRentSignUpWizard, self).post(*args, **kwargs)

    def get_form_kwargs(self, step=None):
        return {
            "0": {"request": self.request},
            "1": {
                "melissa": get_melissa(),
                "activate_correction": True,
                "request": self.request,
                "instances": [self.request.user, self.request.user.profile]
            },
            "2": {
                "melissa": get_melissa(),
                "activate_correction": True,
                "request": self.request,
                "aim": create_aim()
            },
        }[step]

    def get_context_data(self, form, **kwargs):
        context = super(BaseRentSignUpWizard, self).get_context_data(form, **kwargs)

        all_plans = RentalPlan.objects.available_for_signup(self.request)

        free_trial = False
        if "free_trial" in [p.slug for p in all_plans]:
            free_trial = True

        context.update({
                "all_plans": all_plans,
                "free_trial": free_trial,
        })
        if self.steps.current == "2":
            context.update({
                "shipping_info": self.get_cleaned_data_for_step("1"),
                # Need to use ``get_cleaned_data_for_step()`` instead of
                # ``get_all_cleaned_data()`` because form "0" may be excluded from
                # form_list via ``show_rental_plan_form_condition()``
                "rental_plan": self.get_cleaned_data_for_step("0")["rental_plan"],
            })
        return context

    def get_template_names(self):
        step = self.steps.current

        template_name = {
            "0": "new_rent/dialogs/rent_signup/step0.html",
            "1": "new_rent/dialogs/rent_signup/step1.html",
            "2": "new_rent/dialogs/rent_signup/step2.html",
        }[step]
        return [template_name]

    def render_payment_failure(self, billing_form, message):
        billing_form._errors = {"__all__": [message]}
        res = self.render(billing_form)
        return res

    def rent_signup(self, form_list):
        rental_plan_form, profile_user_form, billing_form = form_list
        member_rental_plan = rent_signup_for_member(
            self.request,
            rental_plan_form,
            profile_user_form,
            billing_form
        )
        return member_rental_plan

    def after_done(self, form_list, member_rental_plan):
        member_rental_plan.send_plan_subscription_successfull_email()

        self.request.session['just_did_it'] = True

        if self.request.is_ajax():
            return JsonResponse({'redirect_to': reverse('rent:confirmation')})
        else:
            return redirect('rent:confirmation')

    def render_done(self, form, **kwargs):
        try:
            return super(BaseRentSignUpWizard, self).render_done(form, **kwargs)
        # The only error we could expect is PaymentError, if so going
        # one step back and displaying error message
        except PaymentError, exc:
            billing_form = self.get_form(step="2",
                data=self.storage.get_step_data("2"),
                files=self.storage.get_step_files("2"))
            return self.render_payment_failure(billing_form, exc.message)

    def done(self, form_list, **kwargs):
        member_rental_plan = self.rent_signup(form_list)
        return self.after_done(form_list, member_rental_plan)


class NonMemberRentSignUpWizard(BaseRentSignUpWizard):
    form_list = [RentalPlanForm, ProfileAndShippingCreationForm, BillingForm]

    def get_form_kwargs(self, step=None):
        return {
            "0": {"request": self.request},
            "1": {
                "melissa": get_melissa(),
                "activate_correction": True,
                "request": self.request,
            },
            "2": {
                "melissa": get_melissa(),
                "activate_correction": True,
                "request": self.request,
                "aim": create_aim()
            },
        }[step]

    def rent_signup(self, form_list):
        # Workarround for ``show_rental_plan_form_condition()``
        if len(form_list) == 3:
            rental_plan_form, profile_user_form, billing_form = form_list
        else:
            profile_user_form, billing_form = form_list
            rental_plan_form = self.get_form(step="0",
                data=self.storage.get_step_data("0"),
                files=self.storage.get_step_files("0")
            )
            assert rental_plan_form.is_valid()
        # --
        member_rental_plan = rent_signup_for_new_user(
            self.request,
            rental_plan_form,
            profile_user_form,
            billing_form
        )
        return member_rental_plan

    def after_done(self, form_list, member_rental_plan):
        if len(form_list) == 3:
            _rental_plan_form, profile_user_form, _billing_form = form_list
        else:
            profile_user_form, _billing_form = form_list
        # need only for new members
        login(self.request, authenticate(
                username=member_rental_plan.user.username,
                password=profile_user_form.cleaned_data["password"]))

        return super(NonMemberRentSignUpWizard, self).after_done(form_list, member_rental_plan)


class MemberRentSignUpWizard(BaseRentSignUpWizard):
    form_list = [RentalPlanForm, ProfileAndShippingChangeForm, BillingForm]

    def get_context_data(self, form, **kwargs):
        context = super(MemberRentSignUpWizard, self).get_context_data(form, **kwargs)
        if self.steps.current == "1":
            context.update({"user": self.request.user})
        return context

    def get_form_instance(self, step):
        if step == "2":
            try:
                billing_card = BillingCard.objects.get(user=self.request.user)
            except BillingCard.DoesNotExist:
                billing_card = None
            return billing_card

    def get_form_kwargs(self, step=None):
        return {
            "0": {"request": self.request},
            "1": {
                "melissa": get_melissa(),
                "activate_correction": True,
                "request": self.request,
                "instances": [self.request.user, self.request.user.profile]
            },
            "2": {
                "melissa": get_melissa(),
                "activate_correction": True,
                "request": self.request,
                "aim": create_aim()
            },
        }[step]


def rent_sign_up_wizard_factory(request, *args, **kwargs):
    """
    Object factory that returns concrete ``RentSignUpWizard``.

    If user is authenticated returns ``MemberRentSignUpWizard.as_view()``,
    Otherwise ``NonMemberRentSignUpWizard.as_view()``.
    """
    if request.user.is_authenticated():
        return MemberRentSignUpWizard.as_view()(request, *args, **kwargs)
    else:
        return NonMemberRentSignUpWizard.as_view()(request, *args, **kwargs)
