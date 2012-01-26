from logging import debug #@UnusedImport
import decimal

from django.db import transaction
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import login, authenticate
from django import forms

from django_snippets.forms.base_ajax_wizard import BaseAjaxWizard
from django_snippets.views.json_response import JsonResponse

from project.members.forms.account import NameAndAddressForm
from project.buy_orders.models import BuyOrder
from project.members.forms.signup import ProfileAndShippingForm, BillingForm
from project.members.models import Profile, ProfileEntryPoint, BillingHistory,\
    TransactionType, TransactionStatus
from project.utils import create_aim


def title(text):
    def decorator(klass):
        setattr(klass, 'title', text)
        return klass
    return decorator


def get_melissa():
    if settings.MELISSA_CONFIG['use_melissa']:
        from melissadata import Melissa
        return Melissa(settings.MELISSA_CONFIG)
    else:
        return None




@title('Billing')
class CheckoutForm(BillingForm):
    def clean(self):
        data = super(CheckoutForm, self).clean(skip_card_verification=True)
        if not self._errors:
            request = self.request
            user = request.user
            if not user.is_authenticated():
                p = Profile.create(request, None, entry_point=ProfileEntryPoint.Buy)
            else:
                p = user.get_profile()
    
            self.profile = p
                
            order_data = {
                'card_display_number': self.cached_card['display_number'],
                'card_data': self.cached_card['data'],
                'card_type': self.cached_card['type'], 
                'billing_state': self.cached_address['state'],
                'billing_county': self.cached_address.get('county'),}
            
            self.order = BuyOrder.create(request, order_data, p)

            wizard = self.request.checkout_wizard
            f = wizard.get_form(0, self.request.POST)
            f.is_valid() # it's a long way to get info from here
            email = user.email if user.is_authenticated() else f.cleaned_data['email']
            shipping_address = f.cached_address
            shipping_address.update(f.cached_name)
            shipping_address['country'] = 'USA'
            billing_address = self.cached_address
            billing_address.update(self.cached_name)
            billing_address['country'] = 'USA'
            
            self.billing_history = BillingHistory.create(user if user.is_authenticated() else None,
                order_data['card_display_number'], debit=self.order.get_order_total(),
                description = 'Shop Order #%s' % self.order.get_order_number(), 
                reason='buy', type=TransactionType.BuyCheckout)

            if self.order.user:
                invoice_num = 'BUY_%s_%s' % (self.order.user.id, self.billing_history.id)
            else:
                invoice_num = 'BUY_%s' % self.billing_history.id
            
            card = self.cached_card['data']
            aim_data = {
                'number': card['number'], 
                'exp': '/'.join((card['exp_month'], card['exp_year'][-2:])), 
                'code': card['code'],
                'billing': billing_address, 
                'shipping': shipping_address, 
                'invoice_num': invoice_num, 
                'description': self.order.get_aim_description(),
                'x_customer_ip': self.request.META.get('REMOTE_ADDR'),
                'x_email': email,
                'x_po_num': self.order.order_no(),
            }
            if p.user:
                aim_data['x_cust_id'] = p.user.id
            
            self.billing_history.tax = self.order.get_tax_amount()
            self.billing_history.applied_credits = self.order.applied_credits
            aim_data['x_tax'] = self.billing_history.tax 

            self.billing_history.aim_transaction_id = self.order.take_charge(aim_data) 
            
            if self.billing_history.aim_transaction_id or not self.order.get_charge_amount():
                self.billing_history.card_data = self.cached_card['data']
                self.billing_history.save()
                self.order.payment_transaction = self.billing_history
                self.order.save() 
                request.cart.empty()
            else:
                msg = self.order.message
                self.order.delete()
                if p.user:
                    self.billing_history.status = TransactionStatus.Declined
                    self.billing_history.save()
                else:
                    self.billing_history.delete()
                raise forms.ValidationError(msg)
        return data


class AuthenticatedCheckoutWizard(BaseAjaxWizard):
    @staticmethod
    def create(request, initial=None):
        profile = request.user.get_profile()
        shipping_data = profile.get_name_data()
        shipping_data.update(profile.get_shipping_address_data())
        billing_data = profile.get_billing_name_data()
        billing_data.update(profile.get_billing_address_data())
        billing_data.update(profile.get_billing_card_data())
        initial = {
            0: shipping_data,
            1: billing_data,
        }

#        initial[0].update({
#            'first_name': 'pavel',
#            'last_name': 'reznikov',
#            'address1': '312 courthouse sq',
#            'address2': '',
#            'city': 'bay minete',
#            'state': 'AL',
#            'zip_code': '36507',
#        })
#        initial[1].update({
#            'first_name': 'pavel1',
#            'last_name': 'reznikov1',
#            'address1': '312 courthouse sq1',
#            'address2': '1',
#            'city': 'bay minete1',
#            'state': 'AL',
#            'zip_code': '36501',
#        })

        keys = ['0-first_name', '0-last_name', '0-address1', '0-address2', '0-city', '0-state', '0-zip_code']
        shipping_info = dict([(x[2:], request.POST[x]) for x in filter(lambda z: z in keys, request.POST.keys())])
        billing_info = initial.get(1) 
        
        request.checkout_wizard = AuthenticatedCheckoutWizard(
            'cart/checkout/authenticated.html',
            [NameAndAddressForm, CheckoutForm],
            initial=initial,
            title='Checkout', 
            form_kwargs={
                0: {'melissa': get_melissa(), 
                    'activate_correction': True, 
                    'request': request, },
                1: {'melissa': get_melissa(), 
                    'activate_correction': True, 
                    'request': request,
                    'shipping_address': shipping_info,
#                    'billing_address': billing_info,
                    'aim': create_aim(), },
            },
            context={
                'shipping_info': shipping_info,
                'billing_info': billing_info,
            },)
        return request.checkout_wizard

    @transaction.commit_on_success    
    def done(self, request, form_list):
        order = form_list[1].order
        profile = form_list[1].profile

        profile.set_name_data(form_list[0].cached_name)
        profile.set_shipping_address_data(form_list[0].cached_address)
        profile.set_billing_name_data(form_list[1].cached_name, False)
        profile.set_billing_address_data(form_list[1].cached_address, False)
        profile.set_billing_card_data(form_list[1].cleaned_data, True)
        profile.withdraw_store_credits(order.applied_credits)
        profile.save()

        def update(order, data, prefix=''):
            prefix = prefix + '_' if prefix else '' 
            for k, v in data.items():
                setattr(order, prefix + k, v)
        
        update(order, profile.get_billing_name_data(), 'billing')
        update(order, profile.get_billing_address_data(), 'billing')
        update(order, profile.get_name_data())
        update(order, profile.get_shipping_address_data(), 'shipping')

        order.save()
        order.complete()
        
        request.session['successful_buy_order'] = order.id
        if request.is_ajax():
            return JsonResponse({'redirect_to': reverse('buy:confirmation_summary')})
        else:
            return redirect('buy:confirmation_summary')


class NonAuthenticatedCheckoutWizard(BaseAjaxWizard):
    @staticmethod
    def create(request, initial={}):
#        initial = {
#            0: {
#                'email': 'me@trgggoolee5.com',
#                'username': 'troolgggee5',
#                'password': '123123',
#                'confirm_password': '123123',
#                'how_did_you_hear': 1,
#                'first_name': 'pavel',
#                'last_name': 'reznikov',
#                'address1': '312 courthouse sq',
#                'address2': '',
#                'city': 'bay minete',
#                'state': 'AL',
#                'zip_code': '36507',
#            },
#            1: {
#                'first_name': 'pavel',
#                'last_name': 'reznikov',
#                'address1': '65 E central blvd',
#                'address2': '',
#                'city': 'orlando',
#                'state': 'FL',
#                'zip_code': '32801-2401',
#                'number': '4149605050176387',
#                'exp_month': '1',
#                'exp_year': '2011',
#                'code': '123',
#            },
#        }

        keys = ['0-first_name', '0-last_name', '0-address1', '0-address2', '0-city', '0-state', '0-zip_code']
        shipping_info = dict([(x[2:], request.POST[x]) for x in filter(lambda z: z in keys, request.POST.keys())])
        billing_info = initial.get(1) 
        
        request.checkout_wizard = NonAuthenticatedCheckoutWizard(
            'cart/checkout/non_authenticated.html',
            [ProfileAndShippingForm, CheckoutForm],
            initial=initial,
            title='Checkout', 
            form_kwargs={
                0: {'melissa': get_melissa(),
                    'activate_correction': True, 
                    'request': request, },
                1: {'melissa': get_melissa(), 
                    'activate_correction': True, 
                    'request': request,
                    'shipping_address': shipping_info,
                    'aim': create_aim(), },
            },
            context={
                'shipping_info': shipping_info,
                'billing_info': billing_info,
            },)
        return request.checkout_wizard
    
    @transaction.commit_on_success    
    def done(self, request, form_list):
        profile_form = form_list[0].cleaned_data
        
        u = User(username=profile_form['username'], email=profile_form['email'], is_active=True)
        u.set_password(profile_form['password'])
        u.save()
        u = authenticate(email=profile_form['email'], password=profile_form['password'])
        login(request, u)

        profile = form_list[1].profile

        profile.user = u
        profile.how_did_you_hear = profile_form['how_did_you_hear']
        profile.set_name_data(form_list[0].cached_name)
        profile.set_shipping_address_data(form_list[0].cached_address)
        profile.set_billing_name_data(form_list[1].cached_name, False)
        profile.set_billing_address_data(form_list[1].cached_address, False)
        profile.set_billing_card_data(form_list[1].cleaned_data, True)
        profile.save()

        order = form_list[1].order
        order.user = u
        order.applied_credits = decimal.Decimal('0.0')

        form_list[1].billing_history.user = u
        form_list[1].billing_history.save()

        def update(order, data, prefix=''):
            prefix = prefix + '_' if prefix else '' 
            for k, v in data.items():
                setattr(order, prefix + k, v)
        
        update(order, profile.get_billing_name_data(), 'billing')
        update(order, profile.get_billing_address_data(), 'billing')
        update(order, profile.get_name_data())
        update(order, profile.get_shipping_address_data(), 'shipping')

        order.save()
        order.complete()
        
        request.session['successful_buy_order'] = order.id
        request.session['new_customer'] = True
        if request.is_ajax():
            return JsonResponse({'redirect_to': reverse('buy:confirmation_summary')})
        else:
            return redirect('buy:confirmation_summary')
