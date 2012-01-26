from datetime import datetime, timedelta

from django.db.models import Sum, Avg
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse

from django_snippets.views import paged
from django_snippets.views.simple_view import simple_view
from django_snippets.views.json_response import JsonResponse

from project.staff.views import staff_only
from project.buy_orders.models import BuyCart, BuyOrder
from project.catalog.models.item_votes import ItemVote
from project.crm.models import FeedbackifyFeedback
from project.rent.models import RentList, MemberRentalPlan, RentalPlanStatus,\
    RentOrder, RentOrderStatus
from project.inventory.models import Inventory, InventoryStatus, DistributorItem
from project.members.models import Profile
from project.claims.models import Claim
from project.trade.models import TradeOrderItem
from django.db.models.query_utils import Q


@staff_only
@simple_view('staff/customer/view.html')
def view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = Profile.objects.get(user=user)

    if 'impersonate' in request.GET:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('/')

    not_activated_user = not user.is_active and profile.activation_code
    account_is_blocked = not user.is_active and not profile.activation_code
    can_block_account = request.user.is_superuser
    can_change_extra_slots = request.user.is_superuser #or request.user.get_profile().group in [Group.DC_Manager]

    if request.is_ajax():
        status = 'FAIL'
        action = request.REQUEST.get('action')
        if action == 'resend-activation-link':
            if not_activated_user:
                profile.send_email_confirmation_mail()
                status = 'OK'
        elif action == 'block':
            if can_block_account:
                profile.block_account()
                status = 'OK'
        elif action == 'unblock':
            if can_block_account:
                profile.unblock_account()
                status = 'OK'
        elif action == 'add-extra-slot':
            if can_change_extra_slots:
                profile.extra_rent_slots += 1
                profile.save()
                status = 'OK'
        elif action == 'rm-extra-slot':
            if can_change_extra_slots:
                profile.extra_rent_slots -= 1
                if profile.extra_rent_slots < 0:
                    profile.extra_rent_slots = 0
                profile.save()
                status = 'OK'
        elif action == 'reactivate':
            if request.user.is_superuser:
                plan = MemberRentalPlan.get_current_plan(user)
                if plan and plan.status in [RentalPlanStatus.Delinquent, RentalPlanStatus.Collection]:
                    plan.take_delinquent_payment(True)
                status = 'OK'
        return JsonResponse({'status': status})

    last_orders_buy = BuyOrder.list_recent(user)
    last_order_buy = last_orders_buy[0] if last_orders_buy.count() > 0 else None

    last_order_trade = user.tradeorder_set.order_by('-id')
    last_order_trade = last_order_trade[0] if len(last_order_trade) > 0 else None

    last_order_rent = user.rentorder_set.order_by('-id')
    last_order_rent = last_order_rent[0] if len(last_order_rent) > 0 else None

    rent_plan = MemberRentalPlan.get_current_plan(user)
    rent_plan_cancelable = rent_plan and rent_plan.status in [RentalPlanStatus.CanceledP, RentalPlanStatus.Pending, RentalPlanStatus.Delinquent, RentalPlanStatus.Active, RentalPlanStatus.OnHold]

    stat = {
        'buy': {
            'last_date': last_order_buy.create_date if last_order_buy else '',
            'status': 'Active' if last_order_buy else 'Inactive',
            'earned_total': user.buyorder_set.aggregate(Sum('total'))['total__sum'] or 0,
            'earned_avg': user.buyorder_set.aggregate(Avg('total'))['total__avg'] or 0,
        },
        'trade': {
            'last_date': last_order_trade.create_date if last_order_trade else '',
            'status': 'Active' if last_order_trade else 'Inactive',
            'earned_total': user.tradeorder_set.aggregate(Sum('total'))['total__sum'] or 0,
            'earned_avg': user.tradeorder_set.aggregate(Avg('total'))['total__avg'] or 0,
        },
        'rent': {
            'last_date': last_order_rent.date_rent if last_order_rent else '',
            'status': profile.get_rental_status(False),
            'cancelable': rent_plan_cancelable,
            'earned_total': user.billinghistory_set.filter(status=0, type=1).aggregate(Sum('debit'))['debit__sum'] or 0,
            'earned_avg': user.billinghistory_set.filter(status=0, type=1).aggregate(Avg('debit'))['debit__avg'] or 0,
            'rent_plan': rent_plan,
            'hold_until': rent_plan.hold_reactivate_timestamp if (rent_plan and rent_plan.status == RentalPlanStatus.OnHold) else None,
        },
    }
    stat['earned_total'] = (stat['buy']['earned_total'] + stat['trade']['earned_total'] + stat['rent']['earned_total']) / 3
    stat['earned_avg'] = (stat['buy']['earned_avg'] + stat['trade']['earned_avg'] + stat['rent']['earned_avg']) / 3

    last_order = {}
    last_order['buy'] = last_orders_buy
    last_order['trade'] = last_order_trade
    last_order['rent'] = last_order_rent

    buy_cart, created = BuyCart.objects.get_or_create(user=user) #@UnusedVariable
    trade_list = user.tradelist.all()

    return {
        'current_view': 'customer_view',
        'user': user,
        'billing_address': user.get_profile().get_billing_address_data(),
        'stat': stat,
        'last_order': last_order,
        'cart': buy_cart,
        'cart_total': sum([item.get_retail_price() * item.quantity for item in buy_cart.items.all()]),
        'trade_list': trade_list,
        'trade_total': sum([item.get_price() for item in trade_list]),
        'not_activated_user': not_activated_user,
        'account_is_blocked': account_is_blocked,
        'can_block_account': can_block_account,
        'can_change_extra_slots': can_change_extra_slots,
        'claims': Claim.objects.filter(user=user),
    }

@staff_only
def set_password(request, user_id):
    password = request.POST.get('password')
    if password:
        user = get_object_or_404(User, id=user_id)
        user.set_password(password)
        user.save()
    return redirect('staff:customer_view', user.id)

@staff_only
@simple_view('staff/customer/addresses.html')
def addresses(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return {
        'current_view': 'customer_addresses',
        'user': user,
        'shipping_address': user.profile.get_shipping_address_data(),
        'billing_address': user.profile.get_billing_address_data(),
    }

@staff_only
@simple_view('staff/customer/orders.html')
def orders(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return {
        'current_view': 'customer_orders',
        'user': user,
        'buy_orders': user.buyorder_set.order_by('-id'),
        'trade_orders': user.tradeorder_set.order_by('-id'),
        'rent_orders': user.rentorder_set.order_by('-id'),
    }


def _get_rent_list(user, limit=None):
    qs = RentList.get(user)
    if limit:
        qs = qs[:limit]
    res = []
    for q in qs:
        res.append({
            'item': q,
            'in_stock': Inventory.objects.filter(item=q.item, status=InventoryStatus.InStock, buy_only=False).count(),
            'vendor': DistributorItem.objects.filter(item=q.item).exclude(distributor__id=5).count(),
        })
    return res


@staff_only
@simple_view('staff/customer/lists.html')
def lists(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return {
        'current_view': 'customer_lists',
        'user': user,
#        'buy_orders': user.buyorder_set.order_by('-id'),
#        'trade_orders': user.tradeorder_set.order_by('-id'),
        'rent_list': _get_rent_list(user, 10),
    }

@staff_only
@simple_view('staff/customer/rent_list.html')
def rent_list(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return {
        'current_view': 'customer_lists',
        'user': user,
        'rent_list': _get_rent_list(user),
    }

@staff_only
@simple_view('staff/customer/shopping_cart.html')
def shopping_cart(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return {
        'current_view': 'customer_shopping_cart',
        'user': user,
    }

@staff_only
@simple_view('staff/customer/product_reviews.html')
@paged('reviews')
def product_reviews(request, user_id):
    user = get_object_or_404(User, id=user_id)
    reviews = ItemVote.objects.exclude(review=None).filter(user=user).order_by('-timestamp')
    return {
        'current_view': 'customer_product_reviews',
        'user': user,
        'paged_qs': reviews,
    }

@staff_only
@simple_view('staff/customer/product_ratings.html')
@paged('ratings')
def product_ratings(request, user_id):
    user = get_object_or_404(User, id=user_id)
    ratings = ItemVote.objects.filter(review=None, user=user).order_by('-timestamp')
    return {
        'current_view': 'customer_product_ratings',
        'user': user,
        'paged_qs': ratings,
    }

@staff_only
@simple_view('staff/customer/billing_history.html')
@paged('history')
def billing_history(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return {
        'current_view': 'customer_billing_history',
        'user': user,
        'paged_qs': user.billinghistory_set.filter(status__lt=10),
    }


@staff_only
@simple_view('staff/customer/credits_history.html')
@paged('history')
def credits_history(request, user_id):
    user = get_object_or_404(User, id=user_id)

    date_x = datetime.today() - timedelta(30)

    pending_credits = TradeOrderItem.objects.filter(order__user=user, processed=False, order__create_date__gte=date_x).order_by('-order__create_date')
    pending_credits_total = sum(map(lambda x: x.price + x.get_shipping_reimbursements(), pending_credits))

    processed_credits = TradeOrderItem.objects.filter(order__user=user, processed=True, declined=False).order_by('-order__create_date')
    processed_credits_total = sum(map(lambda x: x.get_price_with_bonus(), processed_credits))

    expired_credits = TradeOrderItem.objects.filter(order__user=user).filter(Q(processed=True, declined=True) | Q(order__create_date__lt=date_x)).order_by('-order__create_date')
    expired_credits_total = sum(map(lambda x: x.price + x.get_shipping_reimbursements(), expired_credits))

    return {
        'current_view': 'customer_credits_history',
        'user': user,
        'pending_credits': pending_credits,
        'pending_credits_total': pending_credits_total,
        'processed_credits': processed_credits,
        'processed_credits_total': processed_credits_total,
        'expired_credits': expired_credits,
        'expired_credits_total': expired_credits_total,
        'paged_qs': user.billinghistory_set.filter(status__lt=10),
    }


@staff_only
@simple_view('staff/customer/shipping_problems.html')
@paged('claims')
def shipping_problems(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return {
        'current_view': 'customer_shipping_problems',
        'user': user,
        'paged_qs': user.claim_set.all().order_by('-date'),
    }

@staff_only
@simple_view('staff/customer/feedbacks.html')
@paged('feedbacks')
def feedbacks(request, user_id):
    user = get_object_or_404(User, id=user_id)
    feedbacks = FeedbackifyFeedback.objects.filter(user=user)
    return {
        'title': 'Customer Feedbacks',
        'user': user,
        'paged_qs': feedbacks,
    }


@staff_only
def cancel_rent_account(request, user_id):
    if not request.user.is_superuser:
        raise Http404()

    u = get_object_or_404(User, id=user_id)
    plan = MemberRentalPlan.get_current_plan(u)
    if not plan or plan.status not in [RentalPlanStatus.CanceledP, RentalPlanStatus.Pending, RentalPlanStatus.Delinquent, RentalPlanStatus.Active, RentalPlanStatus.OnHold]:
        return redirect('staff:customer_view', u.id)

    plan.status = RentalPlanStatus.CanceledP
    plan.save()
#    for o in RentOrder.objects.filter(user=u, status=RentOrderStatus.Shipped):
#        o.status = RentOrderStatus.Canceled
#        o.cancel_penalty_payment()
#        o.save()
#        if o.inventory:
#            o.inventory.status = InventoryStatus.Lost
#            o.inventory.save()
    for o in RentOrder.objects.filter(user=u, status=RentOrderStatus.Pending):
        o.status = RentOrderStatus.Canceled
        o.save()
        if o.inventory:
            o.inventory.status = InventoryStatus.InStock
            o.inventory.save()
    return redirect('staff:customer_view', u.id)


@staff_only
@simple_view('staff/customer/emails.html')
@paged('emails')
def emails(request, user_id):
    user = get_object_or_404(User, id=user_id)
    emails = []
    return {
        'title': 'E-mails',
        'user': user,
        'paged_qs': emails,
    }

@staff_only
@simple_view('staff/customer/email.html')
def email(request, user_id, email_id):
    user = get_object_or_404(User, id=user_id)
    email = get_object_or_404(Letter, mailto=user.email, id=email_id)
    return {
        'title': 'E-mail',
        'user': user,
        'email': email,
    }

@staff_only
def email_body(request, user_id, email_id):
    user = get_object_or_404(User, id=user_id)
    email = get_object_or_404(Letter, mailto=user.email, id=email_id)
    return HttpResponse(email.body)

