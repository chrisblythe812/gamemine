from django import forms
from project.rent.models import CancellationReason
import operator


def title(text):
    def decorator(klass):
        setattr(klass, 'title', text)
        return klass
    return decorator


class RentPlanCancellationForm(forms.ModelForm):
    class Meta:
        model = CancellationReason
        fields = ['shipping_to_slow', 'shipping_to_slow', 'too_many_shipping_problems', 
                  'website_is_not_user_friendly', 'switching_to_another_service', 
                  'not_enough_variety_of_games', 'moving_traveling', 'poor_customer_service', 
                  'service_costs_too_much', 'only_signed_up_for_promotion', 'poor_inventory_availability', 
                  'notes']
    
    shipping_to_slow = forms.BooleanField(label='Shipping to slow', required=False)
    too_many_shipping_problems = forms.BooleanField(label='Too many shipping problems', required=False)
    website_is_not_user_friendly = forms.BooleanField(label='Web site is not user friendly', required=False)
    switching_to_another_service = forms.BooleanField(label='Switching to another service', required=False)
    not_enough_variety_of_games = forms.BooleanField(label='Not enough variety of games', required=False)
    moving_traveling = forms.BooleanField(label='Moving/Traveling', required=False)
    poor_customer_service = forms.BooleanField(label='Poor customer service', required=False)
    service_costs_too_much = forms.BooleanField(label='Service costs too much', required=False)
    only_signed_up_for_promotion = forms.BooleanField(label='Only signed up for promotion', required=False)
    poor_inventory_availability = forms.BooleanField(label='Poor inventory availability', required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)
    accept_terms_of_cancellation = forms.BooleanField(label='I accept and understand the terms of cancellation and want to cancel my account',
                                                      error_messages={'required': 'You have to accept terms of cancellation.'})

    def clean(self):
        data = super(RentPlanCancellationForm, self).clean()
        dd = [
            data.get('shipping_to_slow'),
            data.get('too_many_shipping_problems'),
            data.get('website_is_not_user_friendly'),
            data.get('switching_to_another_service'),
            data.get('not_enough_variety_of_games'),
            data.get('moving_traveling'),
            data.get('poor_customer_service'),
            data.get('service_costs_too_much'),
            data.get('only_signed_up_for_promotion'),
            data.get('poor_inventory_availability'),
        ]
        if not reduce(operator.or_, dd):
            raise forms.ValidationError('Please select your Cancellation Reason.')
        return data
    