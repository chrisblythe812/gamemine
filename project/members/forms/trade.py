from django import forms
from django_snippets.forms.us_location_form import USVerifiedLocationForm
from project.members.models import CashOutPaymentMethod

CASH_OUT_PAYMENT_METHODS = (
    (CashOutPaymentMethod.MailCheck, 'Mail me a check'),
    (CashOutPaymentMethod.Paypal, 'Paypal'),
)

class CashOutOrderForm(USVerifiedLocationForm):
    payment_method = forms.IntegerField(widget=forms.widgets.Select(choices=CASH_OUT_PAYMENT_METHODS),
                                        label='Choose a Payment Method:')
    amount = forms.DecimalField(max_digits=12, decimal_places=2,
                                widget=forms.widgets.HiddenInput(),
                                label='Amount You Want to Cash Out:')
