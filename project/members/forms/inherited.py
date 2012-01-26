from django import forms
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm


class SetPasswordForm(DjangoSetPasswordForm):
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput,
                                    error_messages={'required': 'New password is required'})
    new_password2 = forms.CharField(label="Confirmation", widget=forms.PasswordInput,
                                    error_messages={'required': 'Please confirm new password'})
