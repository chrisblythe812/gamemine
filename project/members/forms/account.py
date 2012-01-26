import re

import datetime
from hashlib import md5
from logging import debug #@UnusedImport

from django import forms
from django_snippets.forms.us_location_form import USVerifiedLocationForm

from project.members.models import CREDIT_CARD_TYPES, BillingCard, Profile
from project.rent.models import MemberRentalPlan, RentalPlanStatus
from django.contrib.auth.models import User


def title(text):
    def decorator(klass):
        setattr(klass, 'title', text)
        return klass
    return decorator


@title('Shipping Information')
class NameAndAddressForm(USVerifiedLocationForm):
    first_name = forms.CharField(label='First Name')
    last_name = forms.CharField(label='Last Name')

    def __init__(self, *args, **kwargs):
        if 'melissa' not in kwargs:
            kwargs['melissa'] = self.melissa if hasattr(self, 'melissa') else None
        if 'request' in kwargs:
            self.request = kwargs['request']
            del kwargs['request']
        if 'activate_correction' in kwargs:
            self.activate_correction = kwargs['activate_correction']
            del kwargs['activate_correction']
        else:
            self.activate_correction = False
        super(NameAndAddressForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(NameAndAddressForm, self).clean()

        if not self._errors:
            d = '\n'.join([
                self.cached_address["address1"],
                self.cached_address["address2"],
                self.cached_address["city"],
                self.cached_address["state"],
                self.cached_address["zip_code"],
            ])
            m = md5()
            m.update(d)
            cs = m.hexdigest()
            d = Profile.objects.filter(shipping_checksum=cs).exclude(user=None)
            if hasattr(self, 'request') and self.request.user.is_authenticated():
                d = d.exclude(user__id=self.request.user.id)
            for p in d:
                rp = MemberRentalPlan.get_current_plan(p.user)
                if not p.user.is_active or (rp and rp.status not in [RentalPlanStatus.Pending, RentalPlanStatus.Active, RentalPlanStatus.Delinquent, RentalPlanStatus.OnHold]):
                    raise forms.ValidationError("This address has been used before for account that's no longer active")

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
                }

            if self.activate_correction:
                d1 = '|'.join(map(lambda x: x.strip(), [
                    data['address1'],
                    data['address2'],
                    data['city'],
                    data['state'],
                    data['zip_code'],
                    data['first_name'],
                    data['last_name'],
                ]))
                d2 = '|'.join(map(lambda x: x.strip(), [
                    self.cached_address['address1'],
                    self.cached_address['address2'],
                    self.cached_address['city'],
                    self.cached_address['state'],
                    self.cached_address['zip_code'],
                    self.cached_name['first_name'],
                    self.cached_name['last_name'],
                ]))
                if d1 != d2:
                    self.correction_data = self.cleaned_data
                    self.correction_data.update(self.cached_name)
                    self.correction_data.update(self.cached_address)
                    data = self.data.copy()
                    correction_data = dict([("%s-%s" % (self.prefix, k), v) for (k, v) in self.correction_data.items()])
                    data.update(correction_data)
                    self.data = data
                    raise forms.ValidationError("The address has been formatted according to US Postal standards.")
        return data

class PhoneNameAndAddressForm(NameAndAddressForm):
    phone_number = forms.CharField(max_length=30, label='Phone Number')

    def matches_phone(self,s):
        p = "\(\d\d\d\) \d\d\d-\d\d\d\d"
        m = re.match(p,s)
        if m:
            return len(m.group(0)) == len(s)
        else:
            return False
    def clean_phone_number(self):
        d = self.cleaned_data
        phone_number = d.get('phone_number')
        if not self.matches_phone(phone_number):
            raise forms.ValidationError("Invalid phone number. Use (XXX) XXX-XXXX format")
        return phone_number

CC_QUICK_CHECK = {
    'visa': [
        400765, 400766, 438093, 400908, 400909, 400910, 403527, 403528, 403529, 404589, 405228,
        405282, 405283, 411855, 411857, 425453, 425454, 425455, 425456, 425457, 425463, 425466,
        430115, 430324, 430325, 430326, 433721, 446301, 446302, 446316, 446317, 446418, 446419,
        446324, 446333, 448402, 450952, 460105, 460106, 460107, 460108, 460111, 460112, 460135,
        461090, 461091, 461092, 461093, 461094, 462968, 463660, 463661, 465972, 465975, 472313,
        474121, 474125, 474126, 474413, 474414, 477517, 477521, 477522, 477523, 477524, 477788,
        480321, 484501, 486211, 401661, 402499, 402703, 403169, 403220, 403294, 403511, 403518,
        403701, 403739, 403770, 403937, 403995, 404537, 404654, 404668, 404675, 405031, 405036,
        408067, 408932, 408933, 408941, 408942, 411065, 411066, 411068, 415746, 415747, 419600,
        419601, 422384, 426116, 430730, 430731, 431149, 431582, 431583, 431584, 432732, 432733,
        432734, 435196, 435197, 435531, 435532, 435533, 435535, 435550, 435551, 435555, 435556,
        435562, 435563, 435581, 435591, 438976, 440361, 441682, 441694, 441695, 442347, 443263,
        443699, 446106, 447083, 447901, 448140, 448244, 448247, 448248, 448290, 449380, 452938,
        454888, 460007, 460010, 460011, 461238, 463958, 466131, 468271, 469591, 472776, 472777,
        472792, 472793, 472794, 473099, 473811, 475001, 475002, 475004, 475005, 475006, 475007,
        475010, 475011, 475012, 475013, 475015, 475016, 475018, 475021, 475022, 475023, 475024,
        475025, 475423, 475424, 475425, 475427, 475429, 475431, 485214, 487081, 400832, 423190,
        424163, 424164, 430222, 430223, 431592, 435548, 447475, 447823, 454806, 471820, 471821,
        475599, 476725, 478374, 487093, 406049, 408836, 430926, 478373, 400765, 400766, 400767,
        400768, 400769, 438092, 438093, 438094, 475865, 441669,
    ],
    'master-card': [
        515109, 518919, 514658, 515553, 540768, 543588, 544372, 546532, 510363, 515003, 515040,
        518460, 523097, 524752, 525451, 526372, 528627, 533283, 543767, 544384, 545343, 510257,
        510265, 510689, 511218, 511269, 511440, 511453, 511758, 511765, 511768, 511776, 511787,
        511789, 514100, 515001, 515061, 515062, 515063, 515064, 515065, 515068, 515069, 515070,
        515071, 515072, 515073, 515074, 515075, 515076, 515077, 515086, 515118, 515119, 515120,
        515158, 515282, 515283, 515463, 515511, 515512, 515517, 515518, 515526, 515527, 515530,
        515538, 515545, 515546, 518213, 519287, 521413, 521427, 521428, 521432, 521433, 521447,
        524872, 526236, 526255, 526260, 526262, 526449, 526486, 527487, 527491, 527492, 528036,
        528037, 528088, 528210, 528770, 529274, 529290, 532238, 532989, 532990, 539635, 539636,
        539637, 539694, 545693, 528229, 504507,
    ],
    'american-express': [3702, 3790, 3743],
}

def check_cc_type(type, number):
    m = {'visa': ['4'],
         'master-card': ['5'],
         'american-express': ['3']}
    return (number or '')[:1] in m.get(type, ['0', '1', '2', '6', '7', '8', '9'])


class CreditCardForm(forms.Form):
    type = forms.ChoiceField(choices=CREDIT_CARD_TYPES, label='Card Type')
    number = forms.CharField(min_length=11, max_length=16, label='Card Number')
    exp_year = forms.ChoiceField(choices=[(x, x) for x in xrange(2010, 2021)], label='Expiration Year')
    exp_month = forms.ChoiceField(choices=[(x, x) for x in xrange(1, 13)], label='Expiration Month')
    code = forms.CharField(required=True, label='Card Code')

    def clean_number(self):
        number = self.cleaned_data.get('number', '')
        type = self.cleaned_data.get('type', '')
        for x in CC_QUICK_CHECK.get(type, []):
            if number.startswith(str(x)):
                raise forms.ValidationError('We do not accept prepaid or gift cards.')
        if hasattr(self, 'request'):
            user = self.request.user
            m = md5()
            m.update(number)
            checksum = m.hexdigest()
            if BillingCard.objects.filter(checksum=checksum).exclude(user=user).count():
                raise forms.ValidationError('This credit card is already registered.')
        return number

    def clean(self):
        data = super(CreditCardForm, self).clean()

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
        return data


class ChangeEmailAndPasswordForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(max_length=10, min_length=4, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ChangeEmailAndPasswordForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if self.request:
            if User.objects.filter(email=email).exclude(id=self.request.user.id).count():
                self._errors['email'] = self.error_class(["You've entered an email address that is already registered."])
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password', '')
        confirm_password = self.cleaned_data.get('confirm_password', '')
        if re.match('^\*+$', password):
            return confirm_password
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("The passwords you entered do not match. Please re-enter them.")
        return confirm_password

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

class OnHoldForm(forms.Form):
    d = forms.ChoiceField(label=u"Select Reactivation Date")

    def __init__(self, *args, **kwargs):
        super(OnHoldForm, self).__init__(*args, **kwargs)
        td = datetime.datetime.now()
        tdd = td + datetime.timedelta(days=7)
        l = []
        for i in xrange(24):
            l.append((i, tdd.strftime('%B %d')))
            tdd += datetime.timedelta(days=1)
        self.fields['d'].choices = l

    def cleaned_date(self):
        return datetime.datetime.now() + datetime.timedelta(days=7+int(self.cleaned_data['d']))
