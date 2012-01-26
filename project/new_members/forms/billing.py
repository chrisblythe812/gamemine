from project.utils import forms
from project.members.forms.signup import BillingForm as OldBillingForm
from project.new_members.forms.legacy import BaseLegacyTransformationForm

from project.members.models import BillingCard


class NewBillingForm(forms.ModelForm):
    data = forms.CharField(required=False)
    type = forms.CharField()
    number = forms.CharField()
    exp_year = forms.CharField()
    exp_month = forms.CharField()
    code = forms.CharField()

    class Meta:
        model = BillingCard
        fields = ("address1", "address2", "city", "county",
                  "data", "type", "first_name", "last_name",
                  "state", "zip")

    def __init__(self, *args, **kwargs):
        super(NewBillingForm, self).__init__(*args, **kwargs)
        if self.instance.data:
            self.initial.update({
                "type": self.instance.data.get("type"),
                "number": self.instance.data.get("number"),
                "exp_year": self.instance.data.get("exp_year"),
                "exp_month": self.instance.data.get("exp_month"),
                "code": self.instance.data.get("code"),
            })

    def clean(self):
        self.cleaned_data["data"] = {
            "type": self.cleaned_data.get("type"),
            "number": self.cleaned_data.get("number"),
            "exp_year": self.cleaned_data.get("exp_year"),
            "exp_month": self.cleaned_data.get("exp_month"),
            "code": self.cleaned_data.get("code")
        }

        return self.cleaned_data


class BillingForm(BaseLegacyTransformationForm, OldBillingForm, forms.Form):
    new_form = NewBillingForm

    transform_hash = {
        "zip_code": "zip",
    }

    def get_new_form_kwargs(self, data=None, *args, **kwargs):
        return {"instance": self.instance}

    def clean(self):
        super(BillingForm, self).clean(skip_card_verification=True)
