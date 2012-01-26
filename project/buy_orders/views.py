from logging import debug #@UnusedImport

from django_snippets.views import simple_view
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django_snippets.thirdparty.views.secure import secure
from django_snippets.views.json_response import JsonResponse

from project.buy_orders.models import BuyList, BuyOrder


@simple_view('buy_orders/admin/pending-orders.html')
def pending(request):
    return {
        'title': 'Pending Orders',
    }


def  _buy_action(request):
    if request.is_ajax():
        from project.members.context_processors import core
        list = request.buy_list
        context = {
            'buy_list': list,
        }
        res = {
            'buy_list': {
                'size': list.count(),
            },
            'lists_size': core(request)['lists_size'],
            'html': render_to_string('members/lists/buy_list_grid.html', context, RequestContext(request)),
        }
        return JsonResponse(res)
    return redirect('members:buy_list')


@transaction.commit_on_success
def remove_from_list(request, id):
    filter = {'pk': id}
    if request.user.is_authenticated():
        filter['user'] = request.user
    else:
        filter['session_id'] = request.current_session_id
    item = get_object_or_404(BuyList, **filter)
    item.delete()
    return _buy_action(request)


@login_required
@secure
@simple_view('buy_orders/confirmation_summary.html')
def confirmation_summary(request):
    try:
        order = BuyOrder.objects.get(user=request.user, pk=request.session['successful_buy_order'])
        new_customer = request.session.get('new_customer', False)
        if not settings.DEBUG:
            del request.session['successful_buy_order'] 
            request.session.pop('new_customer', False)
    except:
        return redirect('catalog:index') 
    return {
        'order': order,
        'new_customer': new_customer,
    }
