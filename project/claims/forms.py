from django import forms
from project.claims.models import GameIsDamagedClaim, WrongGameClaim,\
    MailerIsEmptyClaim, DontReceiveClaim, GamemineNotReceiveGameClaim,\
    GamemineNotRecieveTradeGameClaim, WrongTradeValueCreditClaim
from django.contrib.localflavor.us.forms import USStateField, USZipCodeField
from django_snippets.forms.us_location_form import USStateSelect


class ClaimForm(forms.ModelForm):
    @classmethod
    def create(cls, user, item, initial=None):
        instance=cls.Meta.model.get(user, item)
        return cls(instance=instance, initial=None if instance else initial)


class GameIsDamagedForm(ClaimForm):
    class Meta:
        model = GameIsDamagedClaim
        fields = ['game_is_scratched', 'game_skips_playing', 'game_is_cracked']


class WrongGameForm(ClaimForm):
    class Meta:
        model = WrongGameClaim
        fields = ['game_not_in_list', 'game_not_match_white_sleeve']


class MailerIsEmptyForm(ClaimForm):
    class Meta:
        model = MailerIsEmptyClaim
        fields = ['comment']


class DontReceiveForm(ClaimForm):
    class Meta:
        model = DontReceiveClaim
        fields = ['first_name', 'last_name', 'shipping_address1', 'shipping_address2', 
                  'shipping_city', 'shipping_state', 'shipping_zip_code']

    shipping_state = USStateField(widget=USStateSelect(), required=False, label='State')
    shipping_zip_code = USZipCodeField(label='Zip Code')


class GamemineNotRecieveForm(ClaimForm):
    class Meta:
        model = GamemineNotReceiveGameClaim
        fields = ['mailed_date']
    
    mailed_date = forms.DateField(input_formats=['%m-%d-%Y'])


class GamemineNotRecieveTradeGameForm(ClaimForm):
    class Meta:
        model = GamemineNotRecieveTradeGameClaim
        fields = ['service', 'tracking_number']

class WrongTradeValueCreditForm(ClaimForm):
    class Meta:
        model = WrongTradeValueCreditClaim
        fields = ['received', 'expected']
        
    received = forms.CharField(widget=forms.HiddenInput)
