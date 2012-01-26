import logging
from datetime import datetime
import decimal

from django.db import transaction
from django_snippets.views.json_response import JsonResponse
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.models import User
from django.template import loader
from django.template.context import RequestContext
from django.utils import simplejson as json
from django.http import HttpResponse
from django import forms

from django_snippets.forms.base_ajax_wizard import BaseAjaxWizard

from project.members.forms.signup import BillingForm, PaymentPlanForm, \
    ProfileAndShippingForm, ShippingInformationForm, SignupWizardForm, \
    AllPlansPaymentPlanForm
from project.rent.models import MemberRentalPlan, RentalPlan, RentOrder, \
    RentOrderStatus
from project.members.models import Profile, ProfileEntryPoint, BillingHistory, \
    TransactionType, TransactionStatus
from django.contrib.auth import authenticate, login
from project.members.forms.account import CreditCardForm
from project.taxes.models import Tax
from project.utils import create_aim
from project.rent import rentalplan
from project.new_rent.models import (
    RentalPlan as NewRentalPlan, MemberRentalPlan as NewMemberRentalPlan,
    PaymentError)

logger = logging.getLogger(__name__)


def get_melissa():
    if settings.MELISSA_CONFIG['use_melissa']:
        from melissadata import Melissa
        return Melissa(settings.MELISSA_CONFIG)
    else:
        return None


def title(text):
    def decorator(klass):
        setattr(klass, 'title', text)
        return klass
    return decorator


def get_rental_plans_info(request):
    def _(plan):
        return {
            'price_display': RentalPlan.get_price_display(plan),
        }
    return [_(RentalPlan.PlanA), _(RentalPlan.PlanB), _(RentalPlan.PlanD), _(RentalPlan.PlanE)]


def get_all_rental_plans_info(request):
    result = []
    # Campaign #6 -- Commission Junction
    # Campaign #13 -- Neverblue
    if not request.user.is_authenticated() and request.campaign_id in ['6', '13']:
        plans = [RentalPlan.PlanA, RentalPlan.PlanB]
    else:
        plans = [RentalPlan.PlanA, RentalPlan.PlanB, RentalPlan.PlanD,
                 RentalPlan.PlanE, RentalPlan.PlanC]
    for plan in plans:
        _plan = RentalPlan.get_details2(plan, request) or {}
        _plan.update({
            'price_display': RentalPlan.get_price_display(plan),
            'allowed': RentalPlan.get_allowed_games_amount(plan),
            })
        result.append(_plan)
    return result


class FinishRentalPlanForm(BillingForm):
    def clean(self):
        return super(FinishRentalPlanForm, self).clean(skip_card_verification=True)


class NonMemberRentSignUpWizard(BaseAjaxWizard):
    @staticmethod
    @transaction.commit_on_success
    def create(request, initial={}):
        plan = request.POST.get('0-plan')
        if plan is not None:
            plan = plan or '0'
            plan = RentalPlan.get_details(int(plan))

        keys = ['1-first_name', '1-last_name', '1-address1', '1-address2',
                '1-city', '1-state', '1-zip_code']
        shipping_info = dict([(x[2:], request.POST[x]) for x in
                              filter(lambda z: z in keys, request.POST.keys())])
        billing_info = initial.get(2)
        email = request.POST.get('1-email')
        free_trial = False
        all_plans = NewRentalPlan.objects.available_for_signup(request)
        if "free_trial" in [p.slug for p in all_plans]:
            free_trial = True

        request.rent_wizard = NonMemberRentSignUpWizard(
            'members/rent/wizards/non-member-signup.html',
            [PaymentPlanForm, ProfileAndShippingForm, FinishRentalPlanForm],
            initial=initial,
            title='Rental Signup',
            form_kwargs={
                0: {"request": request},
                1: {'melissa': get_melissa(), 'activate_correction': True, },
                2: {'melissa': get_melissa(),
                    'activate_correction': True,
                    'request': request,
                    'email': email,
                    'shipping_address': shipping_info,
                    'aim': create_aim()},
            },
            context={
                'plan': plan,
                'all_plans': all_plans,
                'shipping_info': shipping_info,
                'billing_info': billing_info,
                "free_trial": free_trial,
            }
        )
        return request.rent_wizard

    def done(self, request, form_list):
        payment_plan_form, profile_and_shipping_form, finish_rental_plan_form = form_list

        shipping_data = profile_and_shipping_form.cleaned_data

        kwargs = {}
        for key, _value in shipping_data.items():
            if key in ["username", "email", "password", "phone_number", "how_did_you_hear"]:
                kwargs[key] = shipping_data.pop(key)
        kwargs["phone"] = kwargs.pop("phone_number")
        kwargs["customer_ip"] = request.META["REMOTE_ADDR"]
        kwargs["campaign_id"] = request.campaign_id
        kwargs["sid"] = request.sid
        kwargs["affiliate"] = request.affiliate
        kwargs["plan"] = payment_plan_form.cleaned_data["plan"]

        billing_data = finish_rental_plan_form.cleaned_data

        billing_card_data = {}
        for key, value in billing_data.items():
            if key in ["code", "exp_month", "exp_year", "number", "type"]:
                billing_card_data[key] = value

        try:
            member_reantal_plan = NewMemberRentalPlan.objects.build_and_create(
                shipping_data=shipping_data,
                billing_data=billing_data,
                billing_card_data=billing_card_data,
                **kwargs
                )
        except PaymentError, exc:
            finish_rental_plan_form = form_list[-1]
            finish_rental_plan_form._errors = {"__all__": [exc.message]}
            # Hack for ``BaseAjaxWizard`` and rent signup template
            finish_rental_plan_form.form_error = exc.message
            return self.render(finish_rental_plan_form, request, self.num_steps() - 1)
        else:
            login(request, authenticate(
                    username=member_reantal_plan.user.username,
                    password=kwargs["password"]))
            member_reantal_plan.send_plan_subscription_successfull_email()

        request.session['just_did_it'] = True
        if request.is_ajax():
            return JsonResponse({'goto_url': reverse('members:personalize_your_games')})
        else:
            return redirect('members:personalize_your_games')


class MemberRentSignUpWizard(BaseAjaxWizard):
    @staticmethod
    @transaction.commit_on_success
    def create(request, initial=None):
        plan = request.POST.get('0-plan')
        if plan is not None:
            plan = RentalPlan.get_details(int(plan))
        profile = request.user.get_profile()
        form2_initial = profile.get_billing_data()
        form2_initial.update(profile.get_billing_card_data())
        initial = {
            1: profile.get_shipping_data(),
            2: form2_initial,
        }

        keys = ['1-first_name', '1-last_name', '1-address1', '1-address2',
                '1-city', '1-state', '1-zip_code']
        shipping_info = dict([(x[2:], request.POST[x]) for x in
                              filter(lambda z: z in keys, request.POST.keys())])
        billing_info = form2_initial

        request.rent_wizard = MemberRentSignUpWizard('members/rent/wizards/member-signup.html',
            [PaymentPlanForm, ShippingInformationForm, FinishRentalPlanForm],
            initial=initial,
            title='Rental Signup',
            form_kwargs={
                1: {'melissa': get_melissa(), 'activate_correction': True, },
                2: {'melissa': get_melissa(),
                    'activate_correction': True,
                    'request': request,
                    'shipping_address': shipping_info,
                    'aim': create_aim()},
            },
            context={
                'plan': plan,
                'rental_plans': get_rental_plans_info(request),
                'all_plans': get_all_rental_plans_info(request),
                'shipping_info': shipping_info,
                'billing_info': billing_info,
            })
        return request.rent_wizard

    def done(self, request, form_list):
        profile = form_list[2].profile
        profile.set_name_data(form_list[1].cached_name)
        profile.set_shipping_address_data(form_list[1].cached_address)
        profile.set_billing_name_data(form_list[2].cached_name, False)
        profile.set_billing_address_data(form_list[2].cached_address, False)
        profile.set_billing_card_data(form_list[2].cleaned_data, True)
        profile.save()

        rent_plan = form_list[2].rent_plan
        rent_plan.first_payment = form_list[2].billing_history
        rent_plan.save()
        rent_plan.activate(True)

        if request.is_ajax():
            return JsonResponse({'goto_url': reverse('members:personalize_your_games')})
#            return JsonResponse({'redirect_to': reverse('members:rent_list')})
        else:
            return redirect('members:rent_list')


@title('Billing')
class ConfirmPlanChangingForm(CreditCardForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs['request']
        del kwargs['request']
        self.shipping_address = kwargs.pop('shipping_address', None)
        self.billing_address = kwargs.pop('billing_address', None)
        super(ConfirmPlanChangingForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(ConfirmPlanChangingForm, self).clean()
        if not self._errors:
            request = self.request

            wizard = self.request.rent_wizard

            f = wizard.get_form(0, self.request.POST)
            f.is_valid()  # it's a long way to get info from here

            plan = int(f.cleaned_data['plan'])

            _profile = request.user.get_profile()
            current_plan = MemberRentalPlan.get_current_plan(_profile.user)
            self.current_plan = current_plan

            if current_plan and current_plan.plan == plan:
                self.rent_plan = None
                return data

            card = self.cached_card['data']
            card['display_number'] = self.cached_card['display_number']
            aim_data = {
                'x_customer_ip': self.request.META.get('REMOTE_ADDR'),
                'x_cust_id': _profile.user.id,
                'x_email': _profile.user.email,
            }

            shipping_address = _profile.get_shipping_address_data()
            shipping_address.update(_profile.get_name_data())
            shipping_address['country'] = 'USA'
            billing_address = _profile.get_billing_data()
            billing_address['country'] = 'USA'

            downgrade = current_plan and plan <= current_plan.plan
            self.downgrade = downgrade
            if downgrade:
                return data

            self.rent_plan = MemberRentalPlan.create(_profile.user, plan, downgrade)
            self.billing_history = None

            amount = RentalPlan.get_start_payment_amount(plan)

            #malcala: changs to capture money
            #do_capture = False
            do_capture = True
            if current_plan:
                last_payment = current_plan.get_last_payment()
                if last_payment and last_payment.status == TransactionStatus.Passed:
                    orders = RentOrder.objects.filter(
                        user=current_plan.user,
                        date_rent__gte=current_plan.created
                        ).exclude(status__in=[RentOrderStatus.Prepared, RentOrderStatus.Canceled])
                    if orders.count():
                        if last_payment.debit < amount:
                            amount -= (current_plan.next_payment_amount or
                                       RentalPlan.get_start_payment_amount(current_plan.plan))
                        do_capture = True

            tax = Tax.get_value(billing_address['state'], billing_address['county'])
            tax_amount = decimal.Decimal('%.2f' % (amount * tax / decimal.Decimal('100.0')))

            aim_data['x_tax'] = tax_amount

            self.billing_history = BillingHistory.create(_profile.user, card['display_number'],
                    debit=amount, reason='rent', type=TransactionType.RentPayment)
            self.billing_history.tax = tax_amount

            invoice_num, description = self.rent_plan.get_payment_description(False, self.billing_history.id)
            self.billing_history.description = description
            self.billing_history.save()

            if do_capture:
                res, aim_response, applied_credits, applied_amount = self.rent_plan.take_money(amount, tax_amount, invoice_num, description,
                    card=card, shipping_data=shipping_address, billing_data=billing_address, aim_data=aim_data,
                    profile=_profile)
                self.billing_history.applied_credits = applied_credits
                self.billing_history.status = TransactionStatus.Passed
                self.billing_history.setted = True
            else:
                res, aim_response = self.rent_plan.authorize_money(amount, tax_amount, invoice_num, description,
                    card=card, shipping_data=shipping_address, billing_data=billing_address, aim_data=aim_data)
                self.billing_history.status = TransactionStatus.Authorized
                self.billing_history.setted = False
            if aim_response:
                self.billing_history.aim_transaction_id = aim_response.transaction_id
                self.billing_history.aim_response  = aim_response._as_dict
                self.billing_history.message = aim_response.response_reason_text
            if not res:
                self.billing_history.status = TransactionStatus.Declined
                self.billing_history.save()
                self.rent_plan.delete()
                raise forms.ValidationError(self.rent_plan.status_message)
            self.billing_history.card_data = self.cached_card['data']
            self.billing_history.save()
        return data


class ChangeRentPlanWizard(BaseAjaxWizard):
    @staticmethod
    @transaction.commit_on_success
    def create(request, initial=None, all_plans=False):
        plan = request.POST.get('0-plan')
        if plan is not None:
            plan = RentalPlan.get_details2(int(plan), request)
        profile = request.user.get_profile()
        cc_data = profile.get_billing_card_data()
        initial = {
            1: cc_data,
        }

        if all_plans:
            plan_form = AllPlansPaymentPlanForm
            all_plans_info = get_all_rental_plans_info(request)
        else:
            plan_form = PaymentPlanForm
            all_plans_info = get_all_rental_plans_info(request)

        # Setting context
        # current_rental_plan already here from context processor
        plans = NewRentalPlan.objects.available_for_change(request)
        limited_plans = [p for p in plans if p.out_per_month]
        unlimited_plans = [p for p in plans if not p.out_per_month]
        # ---

        request.rent_wizard = ChangeRentPlanWizard('members/rent/wizards/change_plan.html',
            [plan_form, ConfirmPlanChangingForm],
            initial=initial,
            title='Change Plan',
            form_kwargs={
                0: {'request': request, },
                1: {'request': request,
                    'billing_address': profile.get_billing_data(),
                    'shipping_address': profile.get_shipping_data(),
                },
            },
            context={'plan': plan,
                     'cc_data': profile.get_payment_card() if cc_data['number'] else None,
                     'rental_plans': get_rental_plans_info(request),
                     'all_plans': all_plans_info,
                     "limited_plans": limited_plans,
                     "unlimited_plans": unlimited_plans,
                     })
        return request.rent_wizard

    def done(self, request, form_list):
        if form_list[1].downgrade:
            current_plan = form_list[1].current_plan
            current_plan.scheduled_plan = form_list[0].cleaned_data.get('plan')
            current_plan.save()
        else:
            billing_form = form_list[1].cleaned_data

            rent_plan = form_list[1].rent_plan

            if rent_plan:
                p = request.user.get_profile()
                p.set_billing_card_data(billing_form, True)

                rent_plan.user = p.user
                rent_plan.first_payment = form_list[1].billing_history
                rent_plan.save()
                rent_plan.activate(False)

                orders = RentOrder.objects.filter(user=rent_plan.user, status__in=[RentOrderStatus.Pending, RentOrderStatus.Prepared])
                if orders.count():
                    rent_plan.is_valid()
                    for o in orders:
                        o.date_rent = datetime.now()
                        o.save()

            try:
                prev_plan = form_list[1].current_plan
                orders = RentOrder.objects.filter(user=prev_plan.user, date_rent__gte=prev_plan.created).exclude(status__in=[RentOrderStatus.Prepared, RentOrderStatus.Canceled])
                if prev_plan and orders.count() == 0:
                    prev_plan.refund_first_payment()
            except Exception, e:
                logger.error(e)

        if request.is_ajax():
#            return JsonResponse({'goto_url': reverse('members:personalize_your_games')})
            return JsonResponse({'redirect_to': reverse('members:rent_list')})
        else:
            return redirect('members:rent_list')


class SignUpWizard(BaseAjaxWizard):
    @staticmethod
    def create(request, initial=None, entry_point=ProfileEntryPoint.Direct):
        wizard = SignUpWizard('members/wizards/signup.html',
                            [SignupWizardForm],
                            initial=initial,
                            title='Sign Up',
                            form_kwargs={
                                0: {'melissa': get_melissa(), },
                            },
                            context={})
        wizard.entry_point = entry_point
        return wizard

    @transaction.commit_on_success
    def done(self, request, form_list):
        data = form_list[0].cleaned_data

        _user = User(username=data['username'], email=data['email'], is_active=False)
        _user.set_password(data['password'])
        _user.save()
        if _user:
            _profile = Profile.create(
                request, _user, entry_point=self.entry_point or ProfileEntryPoint.Direct)
            _profile.how_did_you_hear = data['how_did_you_hear']
            _profile.set_name_data(form_list[0].cached_name)
            _profile.send_email_confirmation_mail()

        template_name = 'members/wizards/signup.dialog.html'
        result = loader.render_to_string(template_name, {
                'title': 'Profile Information',
                'step': 2,
                'step_count': 1,
                'email': data['email'],
            }, context_instance=RequestContext(request))
        content = json.dumps({'form': result})
        return HttpResponse(content, mimetype='application/json')
