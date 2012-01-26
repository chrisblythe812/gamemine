from django import forms
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from project.catalog.models import Item
from project.inventory.models import Distributor, Dropship, Purchase
from project.trade.models import TradeOrderItem
from project.members.models import GROUPS, Campaign
from project.rent.models import RentalPlan, RENTAL_PLAN_STATUS

YES_OR_NO = (
    (True, 'Yes'),
    (False, 'No')
)


class DCSelectForm(forms.Form):
    dc = forms.ModelChoiceField(queryset = Dropship.objects.all(), label="DC:", required=True, empty_label=None)

    @staticmethod
    def get_dc(request):    
        dcform, dc = None, None
        if request.method=="POST":
            dcform = DCSelectForm(request.POST)
            if dcform.is_valid():
                dc = dcform.cleaned_data['dc']
                request.session['STAFF_DC'] = dc
                return dcform, dc 

        if 'STAFF_DC' in request.session:
            dc = request.session['STAFF_DC']

        if dc is None:
            _dc = Dropship.objects.all()[:1]
            if _dc:
                dc = _dc[0]

        if dcform is None and dc is not None:
            dcform = DCSelectForm({'dc': dc.id})

        return dcform, dc


class CustomerSearchForm(forms.Form):
    name = forms.CharField(max_length=100, required=False)
    email = forms.CharField(max_length=100, required=False)
    campaign = forms.ModelChoiceField(queryset=Campaign.objects.all(), required=False)
    plan = forms.ModelChoiceField(queryset=RentalPlan.objects.filter(pk__lt=10), required=False)
    joined_from = forms.DateField(required=False, label='Date From')
    joined_till = forms.DateField(required=False, label='Date To')
    buy_orders = forms.ChoiceField(choices=(('', '---------'), (True, 'Yes'), (False, 'No')), required=False, label='Buy')
    trade_orders = forms.ChoiceField(choices=(('', '---------'), (True, 'Yes'), (False, 'No')), required=False, label='Trade')
    zip = forms.CharField(required=False)
    address = forms.CharField(required=False)
    status = forms.ChoiceField(choices=(('', '---------'),) + RENTAL_PLAN_STATUS, required=False)
#    cancellations = forms.ChoiceField(choices=(('', '---------'), (True, 'Yes'), (False, 'No')), required=False, label='Cancellations')


class DCManagementSearchForm(forms.Form):
    dc = forms.ChoiceField(label="By DC:", choices=Dropship.choices(with_all=True), required=False)
    date_from = forms.DateField(label="From:", required=False, input_formats=['%m-%d-%Y'])
    date_to = forms.DateField(label="To:", required=False, input_formats=['%m-%d-%Y'])

    def get_data(self):
        if self.is_valid():
            date_from = self.cleaned_data['date_from']
            date_to = self.cleaned_data['date_to']
            return date_from, date_to
        else:
            return None, None


class PurchaseForm(forms.Form):
    distributor = forms.ChoiceField(label="Distributor", choices=Distributor.choices())
    is_new = forms.BooleanField(required=False, initial=True)


class PurchaseItemForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())
    upc = forms.CharField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(widget=forms.HiddenInput())

PurchaseItemFormSet = forms.formsets.formset_factory(PurchaseItemForm, extra=0, can_delete=True)


class InventoryCheckInForm(forms.Form):
    upc = forms.CharField(widget=forms.HiddenInput())
    quantity = forms.IntegerField()
    purchase = forms.IntegerField(required=False)
    buy_only = forms.BooleanField(required=False)
    condition = forms.ChoiceField(choices=((True, 'NG'), (False, 'UG')), initial=True)
    dc = forms.ModelChoiceField(queryset=Dropship.objects.all())

    def clean_upc(self):
        upc = self.cleaned_data['upc']
        item = Item.find_by_upc(upc)
        if not item:
            raise forms.ValidationError('Wrong UPC')
        return item

    def clean_purchase(self):
        purchase = self.cleaned_data.get('purchase')
        if purchase:
            try:
                purchase = get_object_or_404(Purchase, id=purchase)
            except: 
                raise forms.ValidationError('Wrong Purchase Order')
        return purchase

    def clean(self):
        cleaned_data = self.cleaned_data

        pi = None
        if not self._errors.get('purchase'):
            try:
                purchase = cleaned_data.get('purchase')
                if purchase: 
                    pi = purchase.items.filter(item=cleaned_data['upc'].id)[0]
            except:
                self._errors['purchase'] = self.error_class(['There is no such game in this purchase order.'])

        if pi:
            assigned_quantity = pi.inventory_set.all().count()
            available_quantity = pi.quantity - assigned_quantity
            if available_quantity < cleaned_data.get('quantity'):
                self._errors['quantity'] = self.error_class(['This purchase order contains only %d item(s) of this game.' % pi.quantity])

        cleaned_data['purchase_item'] = pi
        return cleaned_data


class TradeGameForm(forms.ModelForm):

    class Meta:
        model = TradeOrderItem
        fields = ['is_complete', 'is_match', 'is_damaged', 'is_exellent', 'is_like_new', 
                  'is_exellent', 'is_like_new', 'is_very_good', 'is_factory_sealed', 'is_broken', 
                  'is_unplayable', 'is_lightly_scratched', 'is_heavily_scratched', 'is_refurblished', 
                  'is_mailback'] 

    def __init__(self, *args, **kwargs):
        super(TradeGameForm,self).__init__(*args, **kwargs)
        self.fields['is_complete'].label = u'Complete game?'
        self.fields['is_complete'].widget = forms.RadioSelect(choices=YES_OR_NO)

        self.fields['is_match'].label = u'Does game received match order?'
        self.fields['is_match'].widget = forms.RadioSelect(choices=YES_OR_NO)

        self.fields['is_damaged'].label = u'Game received is damaged?'
        self.fields['is_damaged'].widget = forms.RadioSelect(choices=YES_OR_NO)

        self.fields['is_exellent'].label = u'Exellent'
        self.fields['is_like_new'].label = u'Like New'
        self.fields['is_very_good'].label = u'Very Good'
        self.fields['is_factory_sealed'].label = u'Factory Sealed'
        self.fields['is_broken'].label = u'Broken'
        self.fields['is_unplayable'].label = u'Unplayable'
        self.fields['is_lightly_scratched'].label = u'Lightly Scratched'
        self.fields['is_heavily_scratched'].label = u'Heavily Scratched'
        self.fields['is_refurblished'].label = u'Can the game be refurbished?'
        self.fields['is_refurblished'].widget = forms.RadioSelect(choices=YES_OR_NO)

        self.fields['is_mailback'].label = u'Does game qualify for mailback?'
        self.fields['is_mailback'].widget = forms.RadioSelect(choices=YES_OR_NO)


USER_GROUPS = list(GROUPS)
del USER_GROUPS[0]


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active', 'is_superuser']

    role = forms.IntegerField(widget=forms.Select(choices=USER_GROUPS))
    dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), required=False)


class NewUserForm(UserForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'is_superuser']

    role = forms.IntegerField(widget=forms.Select(choices=USER_GROUPS))
    password = forms.CharField(required=True)
