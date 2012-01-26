from logging import debug #@UnusedImport
from datetime import datetime

from django.db.models import Count
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.db import transaction
from django.template.context import RequestContext
from django.forms.models import ModelForm, modelformset_factory,\
    ModelChoiceField
from django.db.models.query_utils import Q

from django_snippets.views import simple_view

from project.rent.models import RentOrder, RentOrderStatus, AllocationFactor,\
    RentOrderPoll
from project.catalog.models.items import Item
from project.inventory.models import Dropship, Inventory, InventoryStatus
from project.staff.views import staff_only, ajax_only
from django.forms.widgets import RadioSelect, CheckboxInput
from django import forms
from django.utils.safestring import mark_safe
from django.http import Http404
from project.crm.models import PersonalGameTicket, CASE_STATUSES_PUBLIC,\
    CaseStatus
import operator
from project.claims.models import Claim, SphereChoice, CLAIM_NORMALIZED_TITLES
from project.members.models import Group


@transaction.commit_on_success
def orders(request, **kwargs):
    message = ''

    if 'cancel' in request.GET:
        order = get_object_or_404(RentOrder, id=int(request.GET['cancel']), status=RentOrderStatus.Prepared)

        inventory_barcode = order.inventory.barcode

        order.inventory = None

        order.status = RentOrderStatus.Pending
        order.date_prepared = None

        order.outgoing_endicia_data = None
        order.outgoing_mail_label = None
        order.outgoing_tracking_number = None
        order.outgoing_tracking_scans = None

        order.incoming_endicia_data = None
        order.incoming_mail_label = None
        order.incoming_tracking_number = None
        order.incoming_tracking_scans = None

        profile = order.user.get_profile()
        dc = Dropship.find_closest_dc(profile.shipping_zip, order.item, profile.dropship)
        if dc:
            order.source_dc = dc

        order.save()

        if RentOrder.objects.filter(inventory__barcode=inventory_barcode, status=RentOrderStatus.Prepared).count() == 0:
            inventory = Inventory.objects.get(barcode=inventory_barcode)
            inventory.status = InventoryStatus.InStock
            inventory.save()

        return redirect('staff:page', 'Rent/Orders')

    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        if barcode:
            try:
                inventory = Inventory.objects.exclude(buy_only=True).get(barcode=barcode,
                                                                         status=InventoryStatus.InStock)
                dc = request.user.get_profile().dc
                if dc and dc.code != inventory.dropship.code:
                    message = 'Barcode "<strong>%s</strong>" doesn\'t found in <strong>%s</strong>.' % (barcode, str(dc))
                else:
                    order = RentOrder.objects.filter(status=RentOrderStatus.Pending,
                                                     source_dc__code=inventory.dropship.code,
                                                     item__id=inventory.item.id).order_by('-map')
                    if order.count():
                        order = order[0]
                        order.inventory = inventory
                        order.status = RentOrderStatus.Prepared
                        order.date_prepared = datetime.now()
                        order.prepared_by = request.user
                        order.save()
                        inventory.status = InventoryStatus.Pending
                        inventory.tmp_new_dc_code_aproved = True
                        inventory.save()
                        message = 'Barcode "<strong>%s</strong>" was successfully added to the Prepared List.' % barcode
                    else:
                        message = 'Barcode "<strong>%s</strong>" does not match any item in Picked List.' % barcode
            except Inventory.DoesNotExist, e: #@UnusedVariable
                message = 'Barcode "<strong>%s</strong>" does not exist or not in stock.' % barcode

    picked_list = RentOrder.objects.filter(status=RentOrderStatus.Pending).order_by('item__category', 'source_dc', 'item__short_name')

    if not request.user.is_superuser:
        p = request.user.get_profile()
        if p.dc:
            picked_list = picked_list.filter(source_dc__code=p.dc.code)

    picked_list = picked_list.values('item', 'item__name', 'source_dc').annotate(quantity=Count('item'))
    picked_list = map(lambda x: {
        'item': Item.objects.get(id=x['item']),
        'dropship': x['source_dc'] and Dropship.objects.get(id=x['source_dc']) or None,
        'quantity': x['quantity']
    }, picked_list)

    all_picked_games = reduce(lambda a, b: a + b['quantity'], picked_list, 0)

    prepared_list = RentOrder.objects.filter(status=RentOrderStatus.Prepared).order_by('-date_prepared')
    if not request.user.is_superuser:
        p = request.user.get_profile()
        if p.dc:
            prepared_list = prepared_list.filter(source_dc__code=p.dc.code)

    return {
        'title': 'Rent Orders',
        'message': message,
        'picked_list': picked_list,
        'all_picked_games': all_picked_games,
        'prepared_list': prepared_list,
        'prepared_list_ids': map(lambda x: x.id, prepared_list),
    }, None


@staff_only
@ajax_only
def rent_pick_list_details(request, item_id, dc):
    item = get_object_or_404(Item, id=item_id)
    dc = get_object_or_404(Dropship, id=dc)

    orders = RentOrder.objects.filter(status=RentOrderStatus.Pending, source_dc=dc, item=item)
    orders = orders.order_by('-map').select_related()

    return render_to_response('staff/rent/orders/partials/rent_pick_list_details.html', {
            'item': item,
            'orders': orders,
        }, RequestContext(request))


def orders__shipped(request, **kwargs):
    orders = RentOrder.objects.filter(status=RentOrderStatus.Shipped).order_by('-date_shipped')

    class Form(forms.Form):
        q = forms.CharField(required=False)

    q = request.GET.get('q')
    if q:
        qq = []
        ff = ['incoming_tracking_number', 'outgoing_tracking_number', 'inventory__barcode', 'first_name',
              'last_name', 'item__short_name', 'item__name', 'item__upc']
        for piece in q.split():
            qq += map(lambda f: Q(**{f + '__icontains': piece}), ff)
        orders = orders.filter(reduce(operator.or_, qq))
        if orders.count() == 1:
            return redirect('staff:rent_order_details', orders[0].id)
    else:
        p = request.user.get_profile()
        if p.dc:
            orders = orders.filter(source_dc=p.dc)

    return {
        'title': 'Rent Orders: Shipped',
        'paged_qs': orders,
        'form': Form(initial={'q': q})
    }, None, ('orders', 50)


def create_yes_no_widget():
    return RadioSelect(choices=((True, 'YES'), (False, 'NO')))

class RentOrderPollForm(ModelForm):
    class Meta:
        model = RentOrderPoll
        exclude = ('order', 'returned_personal_game', )
        widgets = {
            'received_match_shipped': create_yes_no_widget(),
#            'returned_personal_game': create_yes_no_widget(),
            'is_damaged': create_yes_no_widget(),
            'game_broken': CheckboxInput(),
            'game_unplayable': CheckboxInput(),
            'game_missing': CheckboxInput(),
        }

class RentOrderReturnForm(forms.Form):
    barcode = forms.CharField(required=True)

    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')

        try:
            order = RentOrder.objects.filter(Q(outgoing_tracking_number=barcode) | Q(incoming_tracking_number=barcode))
            if order.count() == 0:
                inventory = Inventory.objects.get(barcode=barcode)
                order = RentOrder.objects.filter(inventory=inventory).order_by('-date_rent')#, status=RentOrderStatus.Shipped)
                if order.count():
                    order = order[0]
                else:
                    order = None
            else:
                order = order[0]
                inventory = order.inventory

            if not inventory:
                raise forms.ValidationError('There is no inventory found in the database.')
            elif order:
                self.order = order
            else:
                raise forms.ValidationError(mark_safe('Barcode or PLANET ID "<strong>%s</strong>" does not match any shipped game.' % barcode))
        except Inventory.DoesNotExist, _e:
            raise forms.ValidationError(mark_safe('Barcode "<strong>%s</strong>" does not exist or it does not in rent.' % barcode))

        return barcode

class RentOrderReturnFormA(RentOrderReturnForm):
    dc = ModelChoiceField(queryset=Dropship.objects.all(), required=True, error_messages={
        'required': 'Please select DC',
    })


def orders__returns(request, **kwargs):
    message = ''

    dc = request.user.get_profile().dc
    if dc:
        FormClass = RentOrderReturnForm
    else:
        FormClass = RentOrderReturnFormA

    if request.method == 'POST':
        POST = request.POST.copy()
        c = POST.get('barcode')
        if c == 'Enter "Manually" or "Scan with barcode scanner"':
            POST['barcode'] = ''
        if POST['barcode']:
            form = FormClass(POST)
            if form.is_valid():
                dc = form.cleaned_data.get('dc', dc)
                return redirect('staff:do_rent_returns', form.order.id, dc.code)
        else:
            form = FormClass()
    else:
        form = FormClass()

    orders = RentOrder.objects.filter(status=RentOrderStatus.Returned).order_by('-date_returned')

    if not request.user.is_superuser:
        p = request.user.get_profile()
        if p.dc:
            orders = orders.filter(Q(return_accepted_by__profile__dc=p.dc) | Q(returned_to_dc=p.dc))

    return {
        'title': 'Rent Orders: Returns',
        'message': message,
        'paged_qs': orders,
        'form': form,
    }, None, ('orders', 50)


@simple_view('staff/rent/orders/return_label.html')
def do_rent_returns(request, order_id, dc):
    dc = get_object_or_404(Dropship, code=dc)
    udc = request.user.get_profile().dc
    if udc and udc != dc:
        raise Http404()

    order = get_object_or_404(RentOrder, id=order_id)
#    if order.status != RentOrderStatus.Shipped:
#        return redirect('staff:page', 'Rent/Orders/Returns')

    lost_claim = order.get_lost_claim()
    damaged_claim = order.get_damaged_claim()
    poll, _c = RentOrderPoll.objects.get_or_create(order=order)
    if request.method == 'POST':
        form = RentOrderPollForm(request.POST, instance=poll)
        if form.is_valid():
            poll = form.save()

            if poll.received_match_shipped:
                if lost_claim:
                    if not poll.is_damaged:
                        order.do_return(dc=dc, user=request.user)
                    else:
                        order.do_return(inventory_status=InventoryStatus.Damaged, dc=dc, user=request.user)
                    return redirect('staff:page', 'Rent/Orders/Returns')

                if damaged_claim:
                    if not poll.is_damaged:
                        """ ticket#84:
                            setting decrease_strike as false
                            documentation was not clear and I didn't get the best information to apply the right fix, so
                            after talking to michael, he told me to change the code just to fix this ticket and nothing else.
                            this is the simplest way to resolve only this issue not affecting anything else.
                        """
                        order.do_return(dc=dc, user=request.user,decrease_strike=False)
                    else:
                        order.do_return(inventory_status=InventoryStatus.Damaged, dc=dc, user=request.user)
                    return redirect('staff:page', 'Rent/Orders/Returns')

                # The game has no any claims
                if not poll.is_damaged:
                    order.do_return(dc=dc, user=request.user)
                    return redirect('staff:page', 'Rent/Orders/Returns')
                # The game is damaged:
                if poll.game_broken or poll.game_unplayable:
                    inventory_status = InventoryStatus.Damaged
                elif poll.game_missing:
                    inventory_status = InventoryStatus.Lost
                else:
                    inventory_status = InventoryStatus.InStock
                order.do_return(inventory_status=inventory_status, dc=dc, user=request.user)
                return redirect('staff:page', 'Rent/Orders/Returns')
            else: # not poll.received_match_shipped
                PersonalGameTicket.create(user=request.user, order=order, message=poll.message)
                return redirect('staff:page', 'Rent/Orders/Returns')
    else:
        form = RentOrderPollForm(instance=poll)

    other_orders = RentOrder.objects.filter(user=order.user, status=RentOrderStatus.Shipped).exclude(id=order.id)

    planet_id = order.incoming_tracking_number
    if planet_id:
        title = 'Return Label - PLANET ID: %s' % planet_id
    else:
        title = 'Return Label - BARCODE: %s' % order.inventory.barcode

    return {
        'title': title,
        'order': order,
        'lost_claim': lost_claim,
        'damaged_claim': damaged_claim,
        'form': form,
        'other_orders': other_orders,
        'dc': dc,
    }


def orders__claims(request, **kwargs):
    return {
        'title': 'Rent Orders: Claims',
    }, None


@staff_only
@transaction.commit_on_success
def mark_shipped(request):
    ids = request.REQUEST.get('ids', '')
    for id in ids.split(','):
        if not id:
            continue
        RentOrder.objects.get(id=int(id)).mark_as_shipped(user=request.user)
    return redirect('staff:page', 'Rent/Orders')



def allocation_factors(request, **kwargs):
    class AllocationFactorForm(ModelForm):
        class Meta:
            model = AllocationFactor
            fields = ['value']

    CategoryFormSet = modelformset_factory(AllocationFactor, form=AllocationFactorForm, extra=0)
    if request.method == "POST":
        formset = CategoryFormSet(request.POST, queryset=AllocationFactor.objects.all())
        if formset.is_valid():
            formset.save()
    else:
        formset = CategoryFormSet(queryset=AllocationFactor.objects.all())
    return {
        'title': 'Allocation Factors',
        'formset': formset,
    }, None



@staff_only
@simple_view('staff/rent/orders/details.html')
def order_details(request, order_id):
    order = get_object_or_404(RentOrder, id=order_id)

    class DCField(forms.ModelChoiceField):
        def label_from_instance(self, obj):
            return obj.code

    class Form(forms.Form):
        dc = DCField(queryset=Dropship.objects.all(), label='Re-send from')

    p = request.user.get_profile()

    can_be_resent = order.status == RentOrderStatus.Shipped and (request.user.is_superuser or p.group in [Group.DC_Manager, Group.DC_Operator])

    form = None
    if can_be_resent or request.user.is_superuser:
        dc = p.dc
        if request.method == 'POST':
            if not dc:
                form = Form(request.POST)
                if not form.is_valid():
                    return redirect('staff:rent_order_details', order.id)
                dc = form.cleaned_data['dc']

            Claim.list(order).delete()

            data = order.user.get_profile().get_name_data()
            data.update(order.user.get_profile().get_shipping_address_data(prefix='shipping'))
            map(lambda k: setattr(order, *k), data.items())

            order.outgoing_endicia_data = None
            order.outgoing_mail_label = None
            order.outgoing_tracking_number = None
            order.outgoing_tracking_scans = None

            order.incoming_endicia_data = None
            order.incoming_mail_label = None
            order.incoming_tracking_number = None
            order.incoming_tracking_scans = None

            order.status = RentOrderStatus.Prepared
            order.date_prepared = datetime.now()
            order.prepared_by = request.user
            order.source_dc = dc

            order.date_shipped = None
            order.date_delivered = None
            order.date_shipped_back = None
            order.date_returned = None

            order.add_event('The order was re-sent by %s from %s DC' % (p.get_name_display(), dc.code))
            order.save()

            order.inventory.dropship = dc
            order.inventory.status = InventoryStatus.Pending
            order.inventory.tmp_new_dc_code_aproved = True
            order.inventory.save()

            return redirect('staff:page', 'Rent/Orders')
        else:
            if not dc:
                dc = order.user.get_profile().dropship or order.source_dc
                form = Form(initial={'dc': dc.id})

    return {
        'title': 'Rent Order Details: #%s (%s)' % (order.order_no(), order.get_status_display()),
        'order': order,
        'page_class': 'staff-page-rent-order-details',
        'can_be_resent': can_be_resent,
        'form': form,
    }


def claims_and_disputes(request, **kwargs):
    class Form(forms.Form):
        status = forms.ChoiceField(choices=[(None, '-----------')] + list(CASE_STATUSES_PUBLIC), required=False)
        type = forms.ChoiceField(choices=[(None, '-----------')] + list(CLAIM_NORMALIZED_TITLES), required=False)
#        q = forms.CharField(required=False)

    form = Form(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Rent/Claims-and-Disputes')

    claims = Claim.objects.filter(sphere_of_claim=SphereChoice.Rent).order_by('-date')
    status = form.cleaned_data.get('status')
    if status and status != 'None':
        if status == CaseStatus.Closed:
            claims = claims.filter(status__in=[CaseStatus.Closed, CaseStatus.AutoClosed])
        else:
            claims = claims.filter(status=status)
    type = form.cleaned_data.get('type')
    if type and type != 'None':
        claims = claims.filter(type=type)

#    q = form.cleaned_data.get('q')
#    if q:
#        claims = search(claims, q, ['user__first_name', 'user__last_name'])

    return {
        'title': 'Rent: Claims / Disputes',
        'paged_qs': claims,
        'form': form,
    }, None, ('claims', 50)


def dc_maintenance(request, **kwargs):
    from project.management.commands.rent import Command

    Formset = modelformset_factory(model=Dropship, extra=0, can_delete=False,
                                   can_order=False, fields=('enable_for_rent', ))
    if request.method == 'POST':
        formset = Formset(request.POST, queryset=Dropship.objects.all())
        if formset.is_valid():
            formset.save()
            Command().handle_label('move_orders')
            return redirect('staff:page', 'Rent/DC-Maintenance')
    else:
        formset = Formset(queryset=Dropship.objects.all())

    return {
        'title': 'Rent: DC Maintenance',
        'formset': formset,
    }, None
