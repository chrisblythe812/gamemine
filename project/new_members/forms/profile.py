from django.forms.models import save_instance
from django.contrib.auth.forms import (
    UserCreationForm as DjangoUserCreationForm,
)
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from composite_form.forms import CompositeForm

from project.utils import forms
from project.members.forms.signup import (
    ProfileAndShippingForm as OldProfileAndShippingForm,
    ProfileAndShippingChangeForm as OldProfileAndShippingChangeForm
)
from project.new_members.forms.legacy import BaseLegacyTransformationForm
from project.new_members.models import Profile


class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(UserCreationForm, self).__init__(*args, **kwargs)


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("shipping_address1", "shipping_address2", "shipping_city",
                  "shipping_state", "shipping_zip", "phone")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(ProfileForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.request = self.request
        return super(ProfileForm, self).save(commit=commit)


class NewProfileAndShippingCreationForm(CompositeForm):
    """
    Form that handles ``User`` and ``Profile`` data.

    On ``save()`` saves ``User`` and ``Profile`` instances to DB and
    returns ``Profile`` instance.
    """
    form_list = [UserCreationForm, ProfileForm]

    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("Invalid form")
        user_form = self.get_form(UserCreationForm)
        user = user_form.save()
        profile_form = self.get_form(ProfileForm)
        profile_form.instance.user = user
        return profile_form.save()


class NewProfileAndShippingChangeForm(CompositeForm):
    form_list = [UserChangeForm, ProfileForm]

    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("Invalid form")
        user_form = self.get_form(UserChangeForm)
        user = user_form.save()
        profile_form = self.get_form(ProfileForm)
        return profile_form.save()


class ProfileAndShippingLTForm(BaseLegacyTransformationForm):
    transform_hash = {
        "address1": "shipping_address1",
        "address2": "shipping_address2",
        "city": "shipping_city",
        "county": "shipping_county",
        "state": "shipping_state",
        "zip_code": "shipping_zip",
        "password": "password1",
        "confirm_password": "password2",
        "phone_number": "phone",

    }

    def get_new_form_kwargs(self, data=None, *args, **kwargs):
        return {"instances": self.instances}

    @property
    def forms(self):
        return self.model_form.forms


class ProfileAndShippingCreationForm(ProfileAndShippingLTForm, OldProfileAndShippingForm):
    new_form = NewProfileAndShippingCreationForm

    def get_new_form_kwargs(self, data=None, *args, **kwargs):
        return {"request": kwargs.get("request")}


class ProfileAndShippingChangeForm(ProfileAndShippingLTForm, OldProfileAndShippingChangeForm):
    new_form = NewProfileAndShippingChangeForm

    def clean_email(self):
        return self.cleaned_data["email"]

    def clean_username(self):
        return self.cleaned_data["username"]
