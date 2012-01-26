from logging import debug
import itertools

from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template.context import RequestContext
from django_snippets.views.json_response import JsonResponse
from django.core.urlresolvers import reverse
from django.template import loader
from django.template.loader import render_to_string
from django.db import transaction
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages

from django_snippets.views import simple_view
from django_snippets.thirdparty.views.secure import secure
from deferred_messages import add_deferred_message

from project.catalog.models.items import Item
from project.rent.models import RentList, MemberRentalPlan, RentOrder,\
    RentOrderStatus
from project.new_rent.models import MemberRentalPlan as NewMemberRentalPlan, RentalPlan
from project.members.wizards import NonMemberRentSignUpWizard


def add(request, id):
    item = get_object_or_404(Item, pk=id)
    if not request.is_ajax():
        return redirect(item.get_absolute_url())
    if request.method == 'POST':
        res = {}
        if 'move_to_1' in request.POST:
            RentList.add_to_list(request, item, True)
            if not request.user.is_authenticated():
                return JsonResponse({'goto_url': reverse('new_rent:sign_up')})
            res['redirect_to'] = reverse('members:rent_list')
        else:
            added_at = RentList.add_to_list(request, item)
            if not request.user.is_authenticated():
                return JsonResponse({'goto_url': reverse('new_rent:sign_up')})
            other_games = item.rent_games_like_this(5, user=request.user)
            context = {
                'item': item,
                'other_games': other_games,
                'added_at': added_at,
                'item_rent_status': item.get_rent_status(request.user),
            }
            res['form'] = loader.render_to_string('rent/dialogs/add.dialog.html',
                                                  context,
                                                  RequestContext(request))
        return JsonResponse(res)
    elif 'quietly' in request.GET:
        added_at = RentList.add_to_list(request, item)
        if not request.user.is_authenticated():
            return JsonResponse({'goto_url': reverse('new_rent:sign_up')})
        other_games = item.rent_games_like_this(5, user=request.user)
        return render_to_response('rent/dialogs/add.dialog.html', {
            'item': item,
            'other_games': other_games,
            'added_at': added_at,
            'item_rent_status': item.get_rent_status(request.user),
        }, context_instance=RequestContext(request))
    else:
        item_position = RentList.find_position(request, item)
        other_games = item.rent_games_like_this(5, user=request.user)
        return render_to_response('rent/dialogs/add.dialog.html', {
            'item': item,
            'other_games': other_games,
            'added_at': item_position,
            'at_home': item.get_rent_status(request.user) == 'At Home',
            'item_rent_status': item.get_rent_status(request.user),
        }, context_instance=RequestContext(request))


def  _rent_action(request, message=None):
    if request.is_ajax():
        from project.members.context_processors import core
        list = RentList.get(request=request)
        context = {
            'rent_list': list,
        }
        res = {
            'rent_list': {
                'size': list.count(),
            },
            'lists_size': core(request)['lists_size'],
            'html': render_to_string('members/lists/rent_list_grid.html', context, RequestContext(request)),
            'message': message,
        }
        return JsonResponse(res)
    return redirect('members:rent_list')


@transaction.commit_on_success
def remove(request, id):
    filter = {'pk': id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    item = get_object_or_404(RentList, **filter)
    orders = RentOrder.objects.filter(list_item=item, status=RentOrderStatus.Prepared)
    if orders.count():
        message = "This item is being processed right now. It couldn't be deleted."
    else:
        message = ''
        RentOrder.objects.filter(list_item=item).delete()
        item.delete()
    return _rent_action(request, message)


@login_required
@transaction.commit_on_success
def move_up(request, id):
    filter = {'pk': id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    item = get_object_or_404(RentList, **filter)
    a, b = [], []
    r = a
    for i in RentList.get(request=request):
        if i == item:
            if a:
                b = [a[-1]]
                del a[-1]
            r = b
        else:
            r.append(i)
    for order, rr in itertools.izip(itertools.count(1), itertools.chain(a, [item], b)):
        rr.order = order
        rr.save()
    return _rent_action(request)


@login_required
@transaction.commit_on_success
def move_down(request, id):
    filter = {'pk': id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    item = get_object_or_404(RentList, **filter)
    a, b = [], []
    r = a
    for i in RentList.get(request=request):
        if i == item:
            if a:
                del a[-1]
            r = b
        else:
            r.append(i)
    for order, rr in itertools.izip(itertools.count(1), itertools.chain(a, [b[0]], [item], b[1:])):
        rr.order = order
        rr.save()
    return _rent_action(request)


@login_required
@transaction.commit_on_success
def move_to(request, id, pos):
    filter = {'pk': id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    item = get_object_or_404(RentList, **filter)
    r = []
    for i in RentList.get(request=request):
        if i != item:
            r.append(i)
    pos = int(pos)
    r.insert(pos, item)
    for order, rr in itertools.izip(itertools.count(1), r):
        rr.order = order
        rr.save()
    return _rent_action(request)


@login_required
def add_note(request, id):
    filter = {'pk': id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    item = get_object_or_404(RentList, **filter)
    if not request.is_ajax():
        return redirect(item.item.get_absolute_url())
    if request.method == 'POST':
        notes = request.POST.get('notes')
        item.notes = notes
        item.save()
        debug(item.notes)
        return HttpResponse(item.notes)
    return render_to_response('rent/dialogs/notes.dialog.html', {
        'item': item,
    }, context_instance=RequestContext(request))


@login_required
@secure
@simple_view('rent/confirmation_summary.html')
def confirmation(request):
    if not settings.DEBUG and 'just_did_it' not in request.session:
        return redirect('index')
    if 'just_did_it' in request.session:
        del request.session['just_did_it']
    member_plan = NewMemberRentalPlan.objects.get(user=request.user)
    plan = RentalPlan.objects.get(pk=member_plan.plan)

    add_deferred_message(
        request,
        messages.INFO,
        reverse("members:personalize_your_games"),
        extra_tags="link-dialog autotrigger")

    return {
        'plan': plan,
    }
