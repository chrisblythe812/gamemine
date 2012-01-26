from project.utils import forms
from project.new_rent.models import RentalPlan
from project.new_members.forms.profile import ProfileAndShippingChangeForm, ProfileAndShippingCreationForm
from project.new_members.forms.billing import BillingForm


class RentalPlanForm(forms.Form):
    rental_plan = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(RentalPlanForm, self).__init__(*args, **kwargs)

    def clean_rental_plan(self):
        rental_plan = RentalPlan.objects.get(pk=self.cleaned_data["rental_plan"])
        if (self.request.user.is_authenticated() and
                self.request.user.get_profile().get_rental_status() == "Active"):
            available_plans = RentalPlan.objects.available_for_change(self.request)
        else:
            available_plans = RentalPlan.objects.available_for_signup(self.request)

        if rental_plan not in available_plans:
            raise forms.ValidationError("Wrong rental_plan")
        return rental_plan


class ConfirmChangeRentPlanForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ConfirmChangeRentPlanForm, self).__init__(*args, **kwargs)
