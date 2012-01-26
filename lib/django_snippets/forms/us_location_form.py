from django import forms
from django.contrib.localflavor.us.forms import USStateField, USZipCodeField
from django.forms.widgets import Select
from django.contrib.localflavor.us.us_states import STATE_CHOICES


class USStateSelect(Select):
    """
    A Select widget that uses a list of U.S. states/territories as its choices.
    """
    def __init__(self, attrs=None):
        MY_STATE_CHOICES = list(STATE_CHOICES)
        MY_STATE_CHOICES.insert(0, ('', 'Please Select', ))
        super(USStateSelect, self).__init__(attrs, choices=MY_STATE_CHOICES)


class USLocationForm(forms.Form):
    address1 = forms.CharField(label='Address 1')
    address2 = forms.CharField(label='Address 2', required=False)
    city = forms.CharField(label='City')
    state = USStateField(widget=USStateSelect(), required=False, label='State')
    zip_code = USZipCodeField(label='Zip Code')


class USVerifiedLocationForm(USLocationForm):
    def __init__(self, *args, **kwargs):
        if 'melissa' not in kwargs:
            kwargs['melissa'] = None
        self.melissa = kwargs['melissa']
        del kwargs['melissa']
        super(USVerifiedLocationForm, self).__init__(*args, **kwargs)


    def clean(self):
        data = super(USVerifiedLocationForm, self).clean()
        if self.melissa:
            from melissadata import MelissaAddressError
            try:
                self.cached_address = self.melissa.inaccurate_address(**data)
            except MelissaAddressError, e:
                raise forms.ValidationError(e)
        else:
            self.cached_address = data.copy()
        return data
