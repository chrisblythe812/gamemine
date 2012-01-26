from logging import debug #@UnusedImport

from django import forms
from django.core.exceptions import ValidationError

from project.catalog.models import Item
from project.members.forms.account import NameAndAddressForm


class AddItemCompletenessForm(forms.Form):
    completeness = forms.ChoiceField(choices=(('cg', 'Complete Game'), ('ig', 'Incomplete Game')))


class AddressForm(NameAndAddressForm):
    phone = forms.CharField(label='Phone Number')
    
    def __init__(self, *args, **kwargs):
        ac = kwargs.get('activate_correction', False)
        kwargs['activate_correction'] = False
        super(AddressForm, self).__init__(*args, **kwargs)
        self.af_activate_correction = ac

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError('Please supply a phone number so we can contact you if there are any problems fulfilling your order.')
        return phone
    
    def clean(self):
        data = super(AddressForm, self).clean()
        if self.melissa:
            from melissadata import MelissaPhoneError
            try:
                self.cached_phone = self.melissa.inaccurate_phone(data['phone'])
            except MelissaPhoneError, e:
                raise forms.ValidationError(e)
            except Exception, e:
                raise forms.ValidationError(e)

            if self.af_activate_correction:    
                d1 = '|'.join(map(lambda x: x.strip(), [
                    data['address1'],
                    data['address2'],
                    data['city'],
                    data['state'],
                    data['zip_code'],
                    data['first_name'],
                    data['last_name'], 
                    data['phone'], 
                ]))
                d2 = '|'.join(map(lambda x: x.strip(), [
                    self.cached_address['address1'],
                    self.cached_address['address2'],
                    self.cached_address['city'],
                    self.cached_address['state'],
                    self.cached_address['zip_code'],
                    self.cached_name['first_name'],
                    self.cached_name['last_name'], 
                    self.cached_phone, 
                ]))
                if d1 != d2:
                    self.correction_data = self.cleaned_data
                    self.correction_data.update(self.cached_name)
                    self.correction_data.update(self.cached_address)
                    self.correction_data['phone'] = self.cached_phone
                    raise forms.ValidationError('')
        
        else:
            self.cached_phone = data.get('phone')
        return data


def validate_upc(value):
    try:
        Item.objects.get(upc=value)
    except:
        raise ValidationError('Invalid UPC')


class CheckUPCForm(forms.Form):
    upc = forms.CharField(validators=[validate_upc])

