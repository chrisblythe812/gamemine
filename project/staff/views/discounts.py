from logging import debug #@UnusedImport

from django.forms.models import ModelForm, modelformset_factory
from django.db import transaction

from project.discount.models import CommonValues, CategoryDiscount,\
    GenreDiscount, TagDiscount, GroupDiscount
from project.catalog.models.items import Item
from project.catalog.models.categories import Category
from project.catalog.models.genres import Genre
from django_snippets.views import simple_view
from django.shortcuts import redirect


@transaction.commit_on_success
def adjustments(request, **kwargs):
    class AdjustmentForm(ModelForm):
        class Meta:
            model = CommonValues
            fields = ('value', )

    AdjustmentFormSet = modelformset_factory(CommonValues, form=AdjustmentForm, extra=0)
    if request.method == "POST":
        formset = AdjustmentFormSet(request.POST, queryset=CommonValues.objects.all())
        if formset.is_valid():
            formset.save()
            for item in Item.objects.all():
                item.recalc_prices()
    else:
        formset = AdjustmentFormSet(queryset=CommonValues.objects.all())
    
    return {
        'title': 'Adjustments',
        'formset': formset,
    }, None


def platform(request, **kwargs):
    class DiscountForm(ModelForm):
        class Meta:
            model = CategoryDiscount
            fields = ('ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete')

    for c in Category.objects.filter(active=True):
        CategoryDiscount.objects.get_or_create(category=c)

    DiscountFormSet = modelformset_factory(CategoryDiscount, form=DiscountForm, extra=0)
    if request.method == "POST":
        formset = DiscountFormSet(request.POST, queryset=CategoryDiscount.objects.all())
        if formset.is_valid():
            formset.save()
            for item in Item.objects.all():
                item.recalc_prices()
    else:
        formset = DiscountFormSet(queryset=CategoryDiscount.objects.all())

    return {
        'title': 'Price adjustment: by platform',
        'formset': formset,
    }, None


def genre(request, **kwargs):
    class DiscountForm(ModelForm):
        class Meta:
            model = GenreDiscount
            fields = ('ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete')

    for g in Genre.objects.filter():
        GenreDiscount.objects.get_or_create(genre=g)

    DiscountFormSet = modelformset_factory(GenreDiscount, form=DiscountForm, extra=0)
    if request.method == "POST":
        formset = DiscountFormSet(request.POST, queryset=GenreDiscount.objects.all())
        if formset.is_valid():
            formset.save()
            for item in Item.objects.all():
                item.recalc_prices()
    else:
        formset = DiscountFormSet(queryset=GenreDiscount.objects.all())

    return {
        'title': 'Price adjustment: by genre',
        'formset': formset,
    }, None


def tag(request, **kwargs):
    class DiscountForm(ModelForm):
        class Meta:
            model = TagDiscount
            fields = ('ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete')

    DiscountFormSet = modelformset_factory(TagDiscount, form=DiscountForm, extra=0, can_delete=True)
    if request.method == "POST":
        formset = DiscountFormSet(request.POST, queryset=TagDiscount.objects.all())
        if formset.is_valid():
            formset.save()
            for item in Item.objects.all():
                item.recalc_prices()
            formset = DiscountFormSet(queryset=TagDiscount.objects.all())
    else:
        formset = DiscountFormSet(queryset=TagDiscount.objects.all())

    return {
        'title': 'Price adjustment: by tag',
        'formset': formset,
    }, None


@simple_view('staff/discounts/add_tag_discount.html')
def add_tag_discount(request):
    class DiscountForm(ModelForm):
        class Meta:
            model = TagDiscount
            fields = ('tag', 'ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete')

    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            form.save()
            for item in Item.objects.all():
                item.recalc_prices()
            return redirect('staff:page', 'Discounts/Tag')
    else:
        form = DiscountForm()
    return {
        'title': 'Add tag discount',
        'form': form,
    }

    
def group(request, **kwargs):
    class DiscountForm(ModelForm):
        class Meta:
            model = GroupDiscount
            fields = ('ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete')

    DiscountFormSet = modelformset_factory(GroupDiscount, form=DiscountForm, extra=0, can_delete=True)
    if request.method == "POST":
        formset = DiscountFormSet(request.POST, queryset=GroupDiscount.objects.all())
        if formset.is_valid():
            formset.save()
            for item in Item.objects.all():
                item.recalc_prices()
            return redirect('staff:page', 'Discounts/Group')
    else:
        formset = DiscountFormSet(queryset=GroupDiscount.objects.all())

    return {
        'title': 'Price adjustment: by group',
        'formset': formset,
    }, None


@simple_view('staff/discounts/add_group_discount.html')
def add_group_discount(request):
    class DiscountForm(ModelForm):
        class Meta:
            model = GroupDiscount
            fields = ('name', 'items', 'ajdust_percent_new', 'ajdust_percent_used', 'adjust_trade_complete')
            
        def __init__(self, *args, **kwargs):
            super(DiscountForm, self).__init__(*args, **kwargs)
            self.fields['items'].label_from_instance = self.game_label_from_instance

        def game_label_from_instance(self, obj):
            return u'%s - %s (%s)' % (obj.id, obj.short_name, obj.category)

    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            form.save()
            for item in form.instance.items.all():
                item.recalc_prices()
            return redirect('staff:page', 'Discounts/Group')
    else:
        form = DiscountForm()
    return {
        'title': 'Add group discount',
        'form': form,
    }
