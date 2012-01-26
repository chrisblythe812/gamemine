from django_snippets.forms.base_ajax_wizard import BaseAjaxWizard
from django_snippets.views.json_response import JsonResponse
from django.db import transaction
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from project.members.views import get_melissa
from project.members.models import Profile, ProfileEntryPoint
from project.members.forms.signup import BillingForm, ProfileAndShippingForm

class NonAuthenticatedTradeWizard(BaseAjaxWizard):
    @staticmethod
    def create(request, initial=None):
        return NonAuthenticatedTradeWizard('trade/authentication/signup.html',
                                [ProfileAndShippingForm, BillingForm],
                                initial=initial,
                                title='Trade Games',
                                form_kwargs={
                                    0: {'melissa': get_melissa(), },
                                    1: {'melissa': get_melissa(), },
                                },
                                context={})

    @transaction.commit_on_success    
    def done(self, request, form_list):
        profile_form = form_list[0].cleaned_data
        billing_form = form_list[1].cleaned_data

        u = User(username=profile_form['username'], email=profile_form['email'], is_active=False)
        u.set_password(profile_form['password'])
        u.save()
        if u:
            p = Profile.create(request, u, entry_point=ProfileEntryPoint.Trade)
            p.set_name_data(form_list[0].cached_name)
            p.set_shipping_address_data(form_list[0].cached_address)
            p.set_billing_name_data(form_list[1].cached_name, False)
            p.set_billing_address_data(form_list[1].cached_address, False)
            p.set_billing_card_data(billing_form, True)
            p.send_email_confirmation_mail()

        res = {}
        res['close'] = True
        res['redirect_to'] = reverse('members:create_account_complete')
        return JsonResponse(res)
