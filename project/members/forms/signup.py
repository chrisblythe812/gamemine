import re
from logging import debug

from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.db import transaction
from django.core.urlresolvers import reverse

from project.members.models import Profile, HOW_DID_YOU_HEAR_CHOICES as HDYHC,\
    ProfileEntryPoint, CREDIT_CARD_TYPES, BillingCard
from project.rent.models import RentalPlan
from project.members.forms.account import NameAndAddressForm, CC_QUICK_CHECK,\
    check_cc_type
from hashlib import md5
from django.conf import settings

from melissadata import MelissaNameError

from project.new_rent.models import RentalPlan
from project.utils import forms as new_forms


HOW_DID_YOU_HEAR_CHOICES = [('', 'Please Select')] + list(HDYHC)


PLANS = (
    (RentalPlan.PlanA, 'Unlimited Monthly. 1 Game Plan ($11.99/mo)'),
    (RentalPlan.PlanB, 'Unlimited Monthly. 2 Game Plan ($19.99/mo)'),
    (RentalPlan.PlanD, 'Unlimited 3 Months. 2 Game Plan ($59.99/mo)'),
    (RentalPlan.PlanE, 'Unlimited 6 Months. 2 Game Plan ($119.99/mo)'),
)

ALL_PLANS = (
    (RentalPlan.PlanA, 'Unlimited Monthly. 1 Game Plan ($11.99/mo)'),
    (RentalPlan.PlanB, 'Unlimited Monthly. 2 Game Plan ($19.99/mo)'),
    (RentalPlan.PlanC, 'Unlimited Monthly. 3 Game Plan ($29.99/mo)'),
    (RentalPlan.PlanD, 'Unlimited 3 Months. 2 Game Plan ($59.99/mo)'),
    (RentalPlan.PlanE, 'Unlimited 6 Months. 2 Game Plan ($119.99/mo)'),
)


def matches_phone(s):
    p = "\(\d\d\d\) \d\d\d-\d\d\d\d"
    m = re.match(p,s)
    if m:
        return len(m.group(0)) == len(s)
    else:
        return False

def title(text):
    def decorator(klass):
        setattr(klass, 'title', text)
        return klass
    return decorator


@title('Select Plan')
class PaymentPlanForm(forms.Form):
    plan = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(PaymentPlanForm, self).__init__(*args, **kwargs)

    def clean_plan(self):
        plans = RentalPlan.objects.available_for_signup(self.request)
        plans = [p.pk for p in plans]
        if not self.cleaned_data["plan"] in plans:
            raise forms.ValidationError("Invalid plan")
        return self.cleaned_data["plan"]


@title('Select Plan')
class AllPlansPaymentPlanForm(forms.Form):
    plan = forms.ChoiceField(choices=ALL_PLANS)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(AllPlansPaymentPlanForm, self).__init__(*args, **kwargs)

    def clean_plan(self):
        plans = RentalPlan.objects.available_for_change(self.request)
        plans = [p.pk for p in plans]
        if not self.cleaned_data["plan"] in plans:
            raise forms.ValidationError("Invalid plan")
        return self.cleaned_data["plan"]


class ProfileForm(new_forms.Form):
    email = forms.EmailField(label='Email')
    username = forms.CharField(max_length=20, label='User Name')
    phone_number = forms.CharField(max_length=30, label='Phone Number')
    password = forms.CharField(max_length=16, min_length=6, widget=forms.PasswordInput(render_value=True), label='Password')
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput(render_value=True), label='Confirmation')

    def clean_confirm_password(self):
        data = self.cleaned_data
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError('Password Confirmation FAILED!')
        return confirm_password

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(
            "You've entered an email address that is already registered. "
            "If you already are or previously were a member click "
            "<a href='%s'>here</a>" % reverse("members:login"))

    def clean_username(self):
        d = self.cleaned_data
        username = d.get('username')
        if User.objects.filter(username__iexact=username).count():
            raise forms.ValidationError("Username already exists in database.")
        return username

    def clean_phone_number(self):
        d = self.cleaned_data
        phone_number = d.get('phone_number')
        if not matches_phone(phone_number):
            raise forms.ValidationError("Invalid phone number. Use (XXX) XXX-XXXX format")
        return phone_number

    @transaction.commit_on_success
    def save(self, request, entry_point=ProfileEntryPoint.Direct):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        username = self.cleaned_data.get('username')
        phone_number = self.cleaned_data.get('phone_number')
        u = User(username=username,
                 email=email,
                 is_active=False)
        u.set_password(password)
        u.save()
        p = Profile.create(request, u, entry_point=entry_point, phone=phone_number)
        p.save()
        p.send_email_confirmation_mail()
        return u



@title('Shipping Information')
class ShippingInformationForm(NameAndAddressForm):
    pass

@title('Shipping Information')
class ProfileAndShippingForm(ProfileForm, ShippingInformationForm):
    how_did_you_hear = forms.ChoiceField(choices=HOW_DID_YOU_HEAR_CHOICES, required=True, label='Profile',
                                         error_messages={'required': 'Please tell how did you hear about us.'})


@title('Shipping Information')
class ProfileAndShippingChangeForm(ProfileAndShippingForm):
    password = forms.CharField(required=False)
    confirm_password = forms.CharField(required=False)
    email = forms.CharField(required=False)
    username = forms.CharField(required=False)
    how_did_you_hear = forms.CharField(required=False)
    phone_number = forms.CharField(required=False)

    def clean_phone_number(self):
        return self.cleaned_data.get("phone_number")


@title('Billing Information')
class BillingForm(ShippingInformationForm):
    type = forms.ChoiceField(choices=CREDIT_CARD_TYPES, label='Card Type')
    number = forms.CharField(min_length=11, max_length=16, label='Card Number')
    exp_year = forms.ChoiceField(choices=[(x, x) for x in xrange(2011, 2022)], label='Expiration Year')
    exp_month = forms.ChoiceField(choices=[(x, x) for x in xrange(1, 13)], label='Expiration Month')
    code = forms.CharField(required=True, label='Card Code')

    def __init__(self, *args, **kwargs):
        if 'aim' in kwargs:
            self.aim = kwargs['aim']
            del kwargs['aim']
        else:
            self.aim = None
        self.shipping_address = kwargs.pop('shipping_address', None)
        self.email = kwargs.pop('email', None)
        self.card_verification_callback = kwargs.pop('card_verification_callback', None)
        self.request = kwargs['request']
        del kwargs['request']
        self.order = None
        super(BillingForm, self).__init__(*args, **kwargs)

    def clean_number(self):
        number = self.cleaned_data.get('number', '')
        type = self.cleaned_data.get('type', '')
        for x in CC_QUICK_CHECK.get(type, []):
            if number.startswith(str(x)):
                raise forms.ValidationError('We do not accept prepaid or gift cards.')
        return number

    def clean(self, skip_card_verification=False):
        data = super(BillingForm, self).clean()

        if not check_cc_type(data.get('type'), data.get('number')):
            raise forms.ValidationError('Bad card number.')

        if not self._errors:
            self.cached_card = {
                'type': data['type'],
                'display_number': 'XXXX-XXXX-XXXX-' + data['number'][-4:],
                'data': {
                    'type': data['type'],
                    'number': data['number'],
                    'exp_year': data['exp_year'],
                    'exp_month': data['exp_month'],
                    'code': data['code'],
                }
            }

            m = md5()
            m.update(data['number'])
            checksum = m.hexdigest()
            qs = BillingCard.objects.filter(checksum=checksum)
            if self.request.user.is_authenticated():
                qs = qs.exclude(user=self.request.user)
            if qs.count():
                raise forms.ValidationError(
                    "You've entered a Credit Card that is already registered. "
                    "If you already are or previously were a member click "
                    "<a href='%s'>here</a>" % reverse("members:login"))

            billing_address = self.cached_address
            billing_address.update(self.cached_name)
            billing_address['country'] = 'USA'

            m = md5()
            m.update('\n'.join((billing_address.get('address1', ''), billing_address.get('city', ''), billing_address.get('state', ''))))
            checksum = m.hexdigest()

#            qs = BillingCard.objects.filter(address_checksum=checksum)
#            if self.request.user.is_authenticated():
#                qs = qs.exclude(user=self.request.user)
#            if qs.count():
#                raise forms.ValidationError('This address is already registered.')

            card = self.cached_card['data']
            aim_data = {
                'number': card['number'],
                'exp': '/'.join((card['exp_month'], card['exp_year'][-2:])),
                'code': card['code'],
                'billing': billing_address,
                'shipping': self.shipping_address,
            }
            if hasattr(self, 'request'):
                request = self.request
                user = request.user
                if user.is_authenticated():
                    aim_data['x_email'] = user.email
                    aim_data['x_cust_id'] = user.id
            if 'x_email' not in aim_data and hasattr(self, 'email'):
                aim_data['x_email'] = self.email

            if not skip_card_verification:
                def assert_res(res):
                    try:
                        if res.response_code == 1:
                            return
                        if res.response_reason_code in [2, 3, 4]:
                            raise forms.ValidationError('Insufficient funds are available for this transaction.')
                        if res.avs_response == 'U':
                            raise forms.ValidationError('We do not accept prepaid cards.')
                        raise forms.ValidationError('We are unable to process you credit card at this time.')
                    except forms.ValidationError, e:
                        debug(e)
                        raise

                aim_response = None
                if self.card_verification_callback:
                    r = self.card_verification_callback(self, data, aim_data)
                    if r:
                        res, aim_response = r
                        if aim_response:
                            assert_res(aim_response)
                        elif not res:
                            raise forms.ValidationError('We are unable to process you credit card at this time.')
                if not aim_response:
                    invoice_num = 'VER'
                    if hasattr(self, 'request'):
                        request = self.request
                        user = request.user
                        if user.is_authenticated():
                            invoice_num = 'VER_%s' % user.id
                    res = self.aim.authorize(0.01, invoice_num=invoice_num, **aim_data)
                    assert_res(res)
                    self.aim.void(res.transaction_id, aim_data)

        return data


@title('Profile Information')
class SignupWizardForm(ProfileForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    agree_of_terms = forms.BooleanField(error_messages={
        'required': mark_safe('You must acknowledge that you have read and agree to the <a href="/Terms/">Terms of Use</a> to continue.')})
    how_did_you_hear = forms.ChoiceField(choices=HOW_DID_YOU_HEAR_CHOICES, required=True, label='Profile',
                                         error_messages={'required': 'Please tell how did you hear about us.'})

    def __init__(self, *args, **kwargs):
        if 'melissa' in kwargs:
            self.melissa = kwargs['melissa']
            del kwargs['melissa']
        else:
            self.melissa = None
        super(SignupWizardForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(SignupWizardForm, self).clean()

        if not self._errors:
            if self.melissa:
                from melissadata import MelissaNameError
                try:
                    self.cached_name = self.melissa.inaccurate_name(**data)
                except MelissaNameError, e:
                    raise forms.ValidationError(e)
                except Exception, e:
                    raise forms.ValidationError(e[0] % e[1])
            else:
                self.cached_name = {
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone_number': data['phone_number'],
                }
        return data


@title('Profile Information')
class SignupFinishForm(forms.Form):
    pass


@title('Profile Information')
class SignupForm(ProfileForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=30, required=True)
    agree_of_terms = forms.BooleanField(error_messages={
        'required': mark_safe('You must acknowledge that you have read and agree to the <a href="/Terms/">Terms of Use</a> to continue.')})

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(SignupForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(SignupForm, self).clean()

        first_name,last_name = data.get('first_name'),data.get('last_name')
        if settings.MELISSA and first_name and last_name:
            melissa = settings.MELISSA
            try:
                melissa_names = melissa.inaccurate_name(first_name=data['first_name'],last_name=data['last_name'])
                data['fist_name'] = melissa_names['first_name']
                data['last_name'] = melissa_names['last_name']
            except MelissaNameError, e:
                del data['first_name']
                del data['last_name']
                raise forms.ValidationError(e)
            except Exception, e:
                del data['first_name']
                del data['last_name']
                raise forms.ValidationError(e[0] % e[1])
        return data

    @transaction.commit_on_success
    def save(self):
        u = super(SignupForm, self).save(self.request, entry_point=ProfileEntryPoint.Direct)
        if settings.MELISSA:
            name = (self.cleaned_data.get('first_name', '') + ' ' + self.cleaned_data.get('last_name', '')).strip()
            name = settings.MELISSA.inaccurate_name(full_name=name)
            u.first_name = name['first_name']
            u.last_name = name['last_name']
            u.phone_number = self.cleaned_data.get('phone_number', '')
        else:
            u.first_name = self.cleaned_data.get('first_name')
            u.last_name = self.cleaned_data.get('last_name')
            u.phone_number = self.cleaned_data.get('phone_number')
        u.save()
        return u
