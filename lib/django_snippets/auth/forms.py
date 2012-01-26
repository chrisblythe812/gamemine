from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate


class AuthenticationByEmailForm(forms.Form):
    email = forms.EmailField(label=_("Email"))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    remember = forms.BooleanField(label=_("Remember"), required=False)
    next = forms.CharField(required=False, widget=forms.HiddenInput)

    @staticmethod
    def create(*args, **kwargs):
        initial = kwargs.get('initial', {})
        initial['remember'] = initial.get('remeber', True)
        return AuthenticationByEmailForm(*args, **kwargs)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        if request:
            request.session.set_test_cookie()
        super(AuthenticationByEmailForm, self).__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        remember = self.cleaned_data.get('remember')

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter a correct email and password. Note that both fields are case-sensitive."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive or blocked."))

        # TODO: determine whether this should move to its own method.
        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(_("Your Web browser doesn't appear to have cookies enabled. Cookies are required for logging in."))
            
            if not remember:
                self.request.session.set_expiry(0)

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache
