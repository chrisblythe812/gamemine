from logging import debug #@UnusedImport

from django.shortcuts import get_object_or_404, redirect
from django import forms
from django.db import transaction
from django_snippets.views.json_response import JsonResponse
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.core.urlresolvers import reverse

from django_snippets.views import simple_view

from project.members.models import BillingHistory, TransactionType,\
    TransactionStatus, Refund
from project.staff.views import staff_only
from project.taxes.models import ByCountyTax, ByStateTax
from django.http import HttpResponseBadRequest


def transactions(request, **kwargs):
    payments = BillingHistory.objects.filter(type__in=[TransactionType.RentPayment, TransactionType.BuyCheckout], status__lt=10).select_related()
    return {
        'title': 'Payment Transactions',
        'paged_qs': payments,
    }, None, ('payments', 50)


@staff_only
@simple_view('staff/payments/transaction_details.html')
def transaction_details(request, id):
    trans = get_object_or_404(BillingHistory, 
                              id=id, 
                              type__in=[TransactionType.RentPayment, TransactionType.BuyCheckout])
    return {
        'title': 'Transaction Details: %s' % trans.id,
        'trans': trans,
    }
    

@staff_only
@transaction.commit_on_success
@simple_view('staff/payments/refund_transaction.html')
def refund_transaction(request, id):
    if not request.is_ajax():
        return redirect('staff:transaction_details', id)
    
    class RefundForm(forms.ModelForm):
        class Meta:
            model = Refund
            fields = ('amount', 'comment')
    
    trans = get_object_or_404(BillingHistory, 
                              id=id, 
                              type__in=[TransactionType.RentPayment, TransactionType.BuyCheckout],
                              status=TransactionStatus.Passed)
    if not trans.refundable():
        return redirect('staff:transaction_details', id)
    
    if request.method == 'POST':
        form = RefundForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'form': render_to_string('staff/payments/refund_transaction.html', {
                        'title': 'Refund Transaction: %s' % trans.id,
                        'trans': trans,
                        'form': form,
                    }, RequestContext(request)) 
                })
    
        res = trans.refund_transaction(form.cleaned_data['amount'], form.cleaned_data['comment'])
        if res and res.response_code == 1:
            return JsonResponse({'redirect_to': reverse('staff:transaction_details', args=[id])})

        if res:
            error_message = 'Error %s: %s' % (res.response_reason_code, res.response_reason_text)
        else:
            error_message = 'Athorize.net transaction id is unknown!'
        return JsonResponse({
            'form': render_to_string('staff/payments/refund_transaction.html', {
                    'title': 'Refund Transaction: %s' % trans.id,
                    'trans': trans,
                    'form': form,
                    'error_message': error_message,
                }, RequestContext(request)) 
            })
    else:
        form = RefundForm(initial={'amount': trans.get_debit_total()})
    return {
        'title': 'Refund Transaction: %s' % trans.id,
        'trans': trans,
        'form': form,
    }


def taxes__by_county(request, **kwargs):
    taxes = ByCountyTax.objects.all()
    return {
        'title': 'Taxes: By County',
        'taxes': taxes,
    }, None


@simple_view('staff/payments/taxes/edit_tax.html')
def add_county_tax(request):
    class AddTaxForm(forms.ModelForm):
        class Meta:
            model = ByCountyTax
            fields = ('county', 'value', )
            
    if request.method == 'POST':
        form = AddTaxForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'form': render_to_string('staff/payments/taxes/edit_tax.html', {
                        'title': 'Add tax value',
                        'form': form,
                        'form_action': reverse('staff:add_county_tax')
                    }, RequestContext(request)) 
                })
        form.save()
        return JsonResponse({'redirect_to': reverse('staff:page', args=['Payments/Taxes/By-County'])})
    
    form = AddTaxForm()
    return {
        'title': 'Add tax value',
        'form': form,
        'form_action': reverse('staff:add_county_tax')
    }


@simple_view('staff/payments/taxes/edit_tax.html')
def edit_county_tax(request, id):
    class EditTaxForm(forms.ModelForm):
        class Meta:
            model = ByCountyTax
            fields = ('value', )
            
    tax = get_object_or_404(ByCountyTax, id=id)
    if request.method == 'POST':
        form = EditTaxForm(request.POST, instance=tax)
        if not form.is_valid():
            return JsonResponse({
                'form': render_to_string('staff/payments/taxes/edit_tax.html', {
                        'title': 'Edit tax value',
                        'form': form,
                        'form_action': reverse('staff:edit_county_tax', args=[tax.id])
                    }, RequestContext(request)) 
                })
        form.save()
        return JsonResponse({'redirect_to': reverse('staff:page', args=['Payments/Taxes/By-County'])})
    
    form = EditTaxForm(instance=tax)
    return {
        'title': 'Edit tax value',
        'form': form,
        'form_action': reverse('staff:edit_county_tax', args=[tax.id])
    }


def delete_county_tax(request, id):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    tax = get_object_or_404(ByCountyTax, id=id)
    tax.delete()
    return JsonResponse({'redirect_to': reverse('staff:page', args=['Payments/Taxes/By-County'])})


def taxes__by_state(request, **kwargs):
    taxes = ByStateTax.objects.all()
    return {
        'title': 'Taxes: By State',
        'taxes': taxes,
    }, None


@simple_view('staff/payments/taxes/edit_tax.html')
def add_state_tax(request):
    class AddTaxForm(forms.ModelForm):
        class Meta:
            model = ByStateTax
            fields = ('state', 'value', )
            
    if request.method == 'POST':
        form = AddTaxForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'form': render_to_string('staff/payments/taxes/edit_tax.html', {
                        'title': 'Add tax value',
                        'form': form,
                        'form_action': reverse('staff:add_state_tax')
                    }, RequestContext(request)) 
                })
        form.save()
        return JsonResponse({'redirect_to': reverse('staff:page', args=['Payments/Taxes/By-State'])})
    
    form = AddTaxForm()
    return {
        'title': 'Add tax value',
        'form': form,
        'form_action': reverse('staff:add_state_tax')
    }


@simple_view('staff/payments/taxes/edit_tax.html')
def edit_state_tax(request, id):
    class EditTaxForm(forms.ModelForm):
        class Meta:
            model = ByStateTax
            fields = ('value', )
            
    tax = get_object_or_404(ByStateTax, id=id)
    if request.method == 'POST':
        form = EditTaxForm(request.POST, instance=tax)
        if not form.is_valid():
            return JsonResponse({
                'form': render_to_string('staff/payments/taxes/edit_tax.html', {
                        'title': 'Edit tax value',
                        'form': form,
                        'form_action': reverse('staff:edit_state_tax', args=[tax.id])
                    }, RequestContext(request)) 
                })
        form.save()
        return JsonResponse({'redirect_to': reverse('staff:page', args=['Payments/Taxes/By-State'])})
    
    form = EditTaxForm(instance=tax)
    return {
        'title': 'Edit tax value',
        'form': form,
        'form_action': reverse('staff:edit_state_tax', args=[tax.id])
    }


def delete_state_tax(request, id):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    tax = get_object_or_404(ByStateTax, id=id)
    tax.delete()
    return JsonResponse({'redirect_to': reverse('staff:page', args=['Payments/Taxes/By-State'])})
