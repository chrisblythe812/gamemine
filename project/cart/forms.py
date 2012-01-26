from django import forms

class AddItemConditionForm(forms.Form):
    condition = forms.ChoiceField(choices=(('new', 'New'), ('used', 'Used')))
