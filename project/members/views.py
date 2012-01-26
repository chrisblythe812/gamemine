import re
from logging import debug
from datetime import datetime, timedelta
import Image
import os
import decimal

from django.contrib.auth import login as auth_login
from django.conf import settings
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template import loader
from django.http import HttpResponse, Http404
from django.utils import simplejson as json
from django.core.urlresolvers import reverse, resolve
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.template.loader import render_to_string
from django import forms
from django.core.paginator import Paginator
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.utils.safestring import mark_safe

from django_snippets.views import simple_view, JsonResponse, redirect_if_authenticated
from django_snippets.auth.forms import AuthenticationByEmailForm
from django_snippets.thirdparty.views import secure

from project.members.forms import SignupForm, PhoneNameAndAddressForm, RentPlanCancellationForm
from project.members.models import BillingHistory, FavoriteGenre, Profile,\
    PARENTAL_CONTROL, get_avatar_upload_to, PARENTAL_CONTROL_REVIEWS,\
    TransactionStatus, TransactionType, CashOutOrder, CashOutOrderStatus,\
    STORE_CREDIT_RATE
from project.buy_orders.models import BuyCart, BuyOrder, BuyList, BuyOrderItem,\
    BuyOrderStatus
from project.rent.models import RentalPlan, MemberRentalPlan, RentList, RentOrder,\
    RentOrderStatus, RentalPlanStatus, CancellationReason
from project.catalog.models import Category
from project.members.wizards import NonMemberRentSignUpWizard,\
    MemberRentSignUpWizard, ChangeRentPlanWizard, SignUpWizard
from project.cart.forms import AddItemConditionForm
from project.trade.models import TradeListItem, TradeOrder, TradeOrderItem
from project.catalog.models.item_votes import ItemVote
from project.catalog.models.genres import Genre
from project.members.forms.account import ChangeEmailAndPasswordForm, OnHoldForm
from project.claims.views import do_rent_claim, do_trade_claim, do_buy_claim
from project.members.models import ProfileEntryPoint
from project.cart.wizards import BillingForm
from project.members.forms.trade import CashOutOrderForm
from project.banners.models import ListPageBanner
from project.utils import create_aim


def get_melissa():
    if settings.MELISSA_CONFIG['use_melissa']:
        from melissadata import Melissa
        return Melissa(settings.MELISSA_CONFIG)
    else:
        return None


@redirect_if_authenticated('catalog:index')
def login(request):
    if request.is_ajax():
        template = 'members/login.dialog.html'
    else:
        template = 'members/login.html'

    if request.method == "POST":
        form = AuthenticationByEmailForm(data=request.POST, request=request)
        if form.is_valid():
            redirect_to = form.cleaned_data.get('next') or request.META.get('HTTP_REFERER')
            debug('Got %s as redirect destination', redirect_to)
            try:
                redirect_to = re.sub('^[^/]+://[^/]+', '', redirect_to)
                resolve(redirect_to)
            except:
                debug('Cannot resolve %s', redirect_to)
                redirect_to = settings.LOGIN_REDIRECT_URL
            debug('Going to redirect to %s after login', redirect_to)

            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            if request.is_ajax():
                return JsonResponse({
                    'redirect_to': redirect_to,
                })
            else:
                return redirect(redirect_to)
        elif request.is_ajax():
            result = loader.render_to_string(template,
                                             {'form': form, },
                                             RequestContext(request))
            content = json.dumps({'form': result})
            return HttpResponse(content, mimetype='application/json')
    else:
        initial = {'next': request.REQUEST.get('next') or request.META.get('HTTP_REFERER') or ''}
        debug('Redirect to %s after login' % initial['next'])
        form = AuthenticationByEmailForm.create(request=request, initial=initial)

    if request.is_ajax():
        result = loader.render_to_string(template,
                                         {'form': form, },
                                         RequestContext(request))
        content = json.dumps({'form': result})
        return HttpResponse(result, mimetype='application/json')

    context = {
        'form': form,
        'hide_unauthenicated_popups': True,
    }

    return render_to_response(template,
                              context,
                              context_instance=RequestContext(request))


def logout(request):
    if not request.user.is_authenticated():
        return redirect('index')
    from django.contrib.auth import logout
    logout(request)
    redirect_to = request.REQUEST.get('next') or request.META.get('HTTP_REFERER') or ''
    try:
        redirect_to = re.sub('^[^/]+://[^/]+', '', redirect_to)
        resolve(redirect_to)
    except:
        redirect_to = 'index'
    return redirect(redirect_to)


@redirect_if_authenticated('catalog:index')
@simple_view('members/create_account.html')
def create_account(request):
    if request.is_ajax():
        return SignUpWizard.create(request, entry_point=request.session.get('entry_point', ProfileEntryPoint.Direct))(request)

    if request.method == 'POST':
        form = SignupForm(request, request.POST)
        if form.is_valid():
            form.save()
            return redirect('members:create_account_complete')
    else:
        form = SignupForm(request)

    return {
        'form': form,
        'hide_unauthenicated_popups': True,
    }


@redirect_if_authenticated('catalog:index')
@simple_view('members/confirm_registration.html')
def confirm_registration(request, code):
    try:
        p = Profile.objects.get(activation_code=code)
        p.activation_code = None
        p.save()
    except:
        return redirect('catalog:index')
    p.user.is_active = True
    p.user.save()
    if p.entry_point == ProfileEntryPoint.Buy:
        next_url = reverse('members:buy_list')
    elif p.entry_point == ProfileEntryPoint.Trade:
        next_url = reverse('trade:list')
    elif p.entry_point == ProfileEntryPoint.Rent:
        next_url = reverse('members:rent_list')
    else:
        next_url = reverse('catalog:index')
    return {
        'email': p.user.email,
        'next_url': next_url,
    }


@redirect_if_authenticated('catalog:index')
@simple_view('members/create_account_complete.html')
def create_account_complete(request):
    pass


@login_required
@simple_view('members/account/account.html')
def account(request):
    pass


@simple_view('members/password_reset_done.html')
def password_reset_done(request):
    if not request.META.get('HTTP_REFERER', '').endswith(reverse('members:amnesia')):
        return redirect('index')


@secure
@login_required
@simple_view('members/account/name_and_address.html')
def account_name_and_address(request):
    def create_form(data):
        return PhoneNameAndAddressForm(data,
                                  melissa=get_melissa(),
                                  request=request,
                                  activate_correction=True)

    profile = request.user.get_profile()
    if request.method == 'POST':
        form = create_form(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            profile.set_name_data(cleaned_data)
            profile.user.save()
            profile.set_shipping_address_data(form.cached_address)
            profile.set_name_data(form.cached_name)
            profile.phone = cleaned_data['phone_number']
            profile.save()
            profile.send_edit_account_information_mail('shipping information')
            return redirect('members:name_and_address')
        else:
            errors = []
            for n, f in form.fields.items():
                if form.errors.get(n):
                    errors.append(mark_safe(u'Error &mdash; Your %s is incorrect' % f.label))
            e = form.errors.get('__all__')
            if e:
                errors.append(e[0])
            form.form_error = (errors or [None])[0]
            if hasattr(form, 'correction_data'):
                form = create_form(form.correction_data)
                form.correction_warning = True
    else:
        initial = {}
        initial.update(profile.get_shipping_address_data())
        initial.update(profile.get_name_data())
        initial.update({'phone_number':profile.phone})
        form = PhoneNameAndAddressForm(initial=initial)
    return {
        'title': 'Name and Address',
        'form': form,
    }


@secure
@login_required
@simple_view('members/account/payment_method.html')
def account_payment_method(request):
    profile = request.user.get_profile()

    def card_verification_callback(form, cleaned_data, aim_data):
        cc_changed = profile.get_billing_card_data().get('number') != cleaned_data.get('number')

        profile.set_billing_name_data(form.cached_name, False)
        profile.set_billing_address_data(form.cached_address, False)
        profile.set_billing_card_data(cleaned_data, False)

        plan = MemberRentalPlan.get_current_plan(request.user)
        if plan and plan.status in [RentalPlanStatus.Delinquent, RentalPlanStatus.Collection] and cc_changed:
            return plan.take_delinquent_payment(True, profile, aim_data)
        return None

    def create_form(data):
        return BillingForm(data,
                           melissa=get_melissa(),
                           request=request,
                           activate_correction=True,
                           shipping_address=profile.get_shipping_data(),
                           card_verification_callback=card_verification_callback,
                           aim=create_aim())

    if request.method == 'POST':
        form = create_form(request.POST)
        if form.is_valid():
            profile.get_payment_card().save()
            profile.send_edit_account_information_mail('billing information')

            if request.is_ajax():
                return JsonResponse({
                    'redirect_to': request.META['HTTP_REFERER']
                })
            else:
                return redirect('members:payment_method')
        else:
            errors = []
            for n, f in form.fields.items():
                if form.errors.get(n):
                    errors.append(mark_safe(u'Error &mdash; Your %s is incorrect' % f.label))
            e = form.errors.get('__all__')
            if e:
                errors.append(e[0])
            form.form_error = (errors or [None])[0]
            if hasattr(form, 'correction_data'):
                form = create_form(form.correction_data)
                form.correction_warning = True
    else:
        initial = {}
        initial.update(profile.get_billing_card_data())
        billing_name = profile.get_billing_name_data()
#        if not(billing_name['first_name'] or billing_name['last_name']):
#            billing_name = profile.get_name_data()
        initial.update(billing_name)
        billing_address = profile.get_billing_address_data()
#        if not billing_address['address1']:
#            billing_address = profile.get_shipping_address_data()
        initial.update(billing_address)
        form = BillingForm(initial=initial, request=request)
    if request.is_ajax():
        if request.method == 'POST':
            result = loader.render_to_string('members/account/payment_method.dialog.html',
                                             {'form': form, },
                                             RequestContext(request))
            return JsonResponse({'form': result})
        else:
            return render_to_response('members/account/payment_method.dialog.html',
                                      {'form': form},
                                      context_instance=RequestContext(request))
    else:
        return {
            'title': 'Payment Method',
            'form': form,
        }


@secure
@login_required
@simple_view('members/account/login_and_password.html')
def account_login_and_password(request):
    user = request.user
    if request.method == 'POST':
        form  = ChangeEmailAndPasswordForm(request.POST, request=request)
        if form.is_valid():
            user.email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            if not re.match('^\*+$', password):
                debug('set new password: %s', password)
                user.set_password(password)
            user.save()
            user.get_profile().send_edit_account_information_mail('login information')
            return redirect('members:login_and_password')
    else:
        form = ChangeEmailAndPasswordForm(initial={
            'email': user.email,
            'password': '*' * 10,
            'confirm_password': '*' * 10,
        })
    return {
        'title': 'Login/Password',
        'form': form,
    }


@secure
@login_required
@simple_view('members/account/billing_history.html')
def account_billing_history(request):
    history = {}
    qs = BillingHistory.objects.filter(user=request.user,
                                       status__in=[TransactionStatus.Passed],
                                       type__in=[TransactionType.RentPayment, TransactionType.BuyCheckout])
    years = [y.year for y in qs.dates('timestamp', 'year')]
    years.sort()
    months = [m for m in qs.dates('timestamp', 'month')]
    months.sort()
    for m in months:
        history[m] = qs.filter(timestamp__year=m.year, timestamp__month=m.month)

    plan = MemberRentalPlan.get_current_plan(request.user)

    return {
        'title': 'Billing History',
        'price': RentalPlan.get_price_display(plan.plan) if plan else None,
        'membership_terms': RentalPlan.get_membership_terms(plan.plan) if plan else None,
        'years': years,
        'months': months,
        'history': history,
    }


@secure
@login_required
@simple_view('members/account/report_problems_type.html')
def account_report_problems(request):
    pass


@secure
@login_required
@simple_view('members/account/report_problems.html')
def report_claim_type(request, sphere):
    user = request.user
    rent_items = []
    trade_items = []
    buy_items = []
    date_x = datetime.today() - timedelta(30)
    if sphere == 'Rent':
        rent_items = RentOrder.objects.filter(user=user, status__in=[RentOrderStatus.Claim, RentOrderStatus.Shipped])
    elif sphere == 'Trade':
        for order in TradeOrder.objects.filter(user=user, create_date__gte=date_x):
            trade_items += list(order.items.all())
    elif sphere == 'Buy':
        for order in BuyOrder.objects.filter(user=user, create_date__gte=date_x):
            buy_items += list(order.items.all())
    return {
        'title': 'Report Problems',
        'rent_items': rent_items,
        'trade_items': trade_items,
        'buy_items': buy_items,
    }


@secure
@login_required
def report_claim(request, sphere, id):
    user = request.user
    if sphere == 'Rent':
        item = get_object_or_404(RentOrder, user=user, id=id)
        return do_rent_claim(request, item)
    elif sphere == 'Trade':
        item = get_object_or_404(TradeOrderItem, id=id)
        if item.order.user != user:
            raise Http404()
        return do_trade_claim(request, item)
    elif sphere == 'Buy':
        item = get_object_or_404(BuyOrderItem, id=id)
        if item.order.user != user:
            raise Http404()
        return do_buy_claim(request, item)
    raise Http404()


@login_required
@simple_view('members/settings/my_systems.html')
def settings_my_systems(request):
    profile = request.user.get_profile()
    all_categories = Category.list()

    if request.method == 'POST':
        for s in all_categories:
            val = request.POST.get('system-%d' % s.id)
            if val:
                profile.owned_systems.add(s)
            else:
                profile.owned_systems.remove(s)
        profile.save()

    owned_systems = profile.get_owned_systems()
    system_map = {}
    for s in all_categories:
        owned = False
        for os in owned_systems:
            if os.id == s.id:
                owned = True
        system_map[s.slug] = {'id': s.id, 'name': s.description, 'owned': owned}

    systems = [
        system_map['Xbox-Games'],
        system_map['Xbox-360-Games'],
        system_map['GameCube-Games'],
        system_map['Nintendo-DS-Games'],
        system_map['Nintendo-Wii-Games'],
        system_map['PlayStation-2-Games'],
        system_map['Sony-PSP-Games'],
        system_map['PlayStation-3-Games'],
    ]

    return {
        'title': 'My Systems',
        'systems': systems,
    }

@login_required
@simple_view('members/settings/parental_controls.html')
def settings_parental_controls(request):
    class Form(forms.Form):
        parental_control = forms.ChoiceField(PARENTAL_CONTROL)
        parental_control_reviews = forms.ChoiceField(PARENTAL_CONTROL_REVIEWS)

    profile = request.user.get_profile()
    if request.method == 'POST':
        form = Form(request.POST)
        action = request.POST.get('action')
        if form.is_valid():
            if action == 'Cancel':
                profile.parental_control = 0
                profile.parental_control_reviews = 0
            else:
                profile.parental_control = form.cleaned_data['parental_control']
                profile.parental_control_reviews = form.cleaned_data['parental_control_reviews']
            profile.save()
            return redirect('members:settings_parental_controls')
    else:
        form = Form(initial={'parental_control': profile.parental_control,
                             'parental_control_reviews': profile.parental_control_reviews,})
    return {
        'title': 'Parental Controls',
        'form': form,
    }


def list_favorite_genres(user):
    current_rates = list(FavoriteGenre.objects.filter(user=user))
    res = []
    for g in Genre.objects.filter(type=1):
        found = False
        for r in current_rates:
            if g.id == r.genre.id:
                res.append((g, r.rating))
                found = True
                break
        if not found:
            res.append((g, 0))
    return res


@login_required
@simple_view('members/profile/favorite_genre.html')
def profile_favorite_genre(request):
    favorite_genres = list_favorite_genres(request.user)
    return {
        'title': 'Rate Game Genres',
        'favorite_genres': favorite_genres,
    }

@login_required
@transaction.commit_on_success
def rate_genre(request, id, rating):
    genre = get_object_or_404(Genre, id=id)
    if not request.is_ajax():
        return redirect('members:profile_favorite_genre')
    FavoriteGenre.rate(request.user, genre, rating)
    favorite_genres = list_favorite_genres(request.user)
    return JsonResponse({
        'status': 'ok',
        'table': render_to_string('members/profile/favorite_genre.table.html', {
                                        'favorite_genres': favorite_genres,
                                  }, RequestContext(request))
    })


@login_required
def clear_genre_rating(request, id):
    return rate_genre(request, id, 0)


def _list_default_avatars(page):
    images = filter(lambda x: x.endswith('.jpg'),
                    os.listdir(os.path.join(settings.MEDIA_ROOT, 'avatars')))
    images = map(lambda x: os.path.join(settings.MEDIA_URL, "avatars", x), images)
    images.insert(0, os.path.join(settings.STATIC_URL, "user.jpg"))
    paginator = Paginator(images, 15)
    try:
        current_page = paginator.page(page)
    except Exception, _e:
        raise Http404()
    return current_page


def _make_thumb(f, file_name, size=(200, 200)):
    try:
        image = Image.open(f)
        image = image.convert("RGB")
        bbox = image.getbbox()

        w1 = float(bbox[2])
        h1 = float(bbox[3])
        w2 = float(size[0])
        h2 = float(size[1])

        d2 = w2 / h2

        if w1 < d2 * h1:
            l = (1 - w1 / d2 / h1) / 2
            lx, ty, rx, by = 0.0, l, 1.0, 1 - l
        else:
            l = (1 - d2 * h1 / w1) / 2
            lx, ty, rx, by = l, 0.0, 1 - l, 1.0

        crop_box = [int(x) for x in (lx * w1, ty * h1, rx * w1, by * h1)]

        image = image.crop(tuple(crop_box))
        image.load()
        image = image.resize(size, Image.ANTIALIAS)

        image.save(file_name)
    except Exception, e:
        debug(e)
        return None


@login_required
@simple_view('members/profile/profile_image.html')
def profile_image(request):
    class AvatarForm(forms.Form):
        image = forms.ImageField(required=True)

        def clean(self):
            data = self.cleaned_data
            image = data.get('image')
            if image and image.size > 500000:
                self._errors['image'] = self.error_class(['File must be max of 500k'])
            return data


    if request.method == 'POST':
        profile = request.user.get_profile()
        img = request.POST.get('set')
        if img:
            if img.endswith('user.jpg'):
                profile.avatar = None
                profile.save()
            else:
                img = os.path.join(settings.MEDIA_ROOT, 'avatars', img)
                file = File(open(img, 'rb'))

                file_name = get_avatar_upload_to(profile, img)
                default_storage.delete(file_name)
                default_storage.save(file_name, file)

                profile.avatar = file_name
                profile.save()
            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                return redirect('members:profile_image')
        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['image']

            file_name = get_avatar_upload_to(profile, file.name, 'jpg')
            default_storage.delete(file_name)
            _make_thumb(file, os.path.join(settings.MEDIA_ROOT, file_name))
            profile.avatar = file_name
            profile.save()

            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                return redirect('members:profile_image')
    else:
        form = AvatarForm()

    if request.is_ajax():
        return JsonResponse({'success': False})

    return {
        'title': 'Profile Image',
        'default_images': _list_default_avatars(1),
        'form': form,
    }


@login_required
def profile_image_defaults(request):
    try:
        p = int(request.GET.get('p'))
    except:
        p = 1
    default_images = _list_default_avatars(p)
    return render_to_response(
        'members/profile/partials/default_avatars_grid.html', {
            'default_images': default_images,
        }, RequestContext(request))


@login_required
@simple_view('members/profile/game_reviews.html')
def profile_game_reviews(request):
    reviews = ItemVote.objects.exclude(review=None).filter(user=request.user).order_by('-timestamp')
    return {
        'title': 'My Reviews',
        'reviews': reviews,
    }

@login_required
@simple_view('members/profile/game_ratings.html')
def profile_game_ratings(request):
    ratings = ItemVote.objects.filter(review=None, user=request.user).order_by('-timestamp')
    return {
        'title': 'My Ratings',
        'ratings': ratings,
    }


@secure
@login_required
@simple_view('members/history/buy.html')
def buy_history(request):
    history = []
    for order in BuyOrder.objects.filter(user=request.user).exclude(status=BuyOrderStatus.Canceled):
        for item in order.items.all():
            history.append({
                'item': item.item,
                'is_new': item.is_new,
                'order_no': '%08d' % order.id,
                'date': order.create_date,
                'price': item.price,
                'claims': item.claims(),
            })
    return {
        'title': 'Buy History',
        'history': history,
    }


@secure
@login_required
@simple_view('members/history/trade.html')
def trade_history(request):
    history = TradeOrderItem.objects.filter(order__user=request.user, processed_date__gte=datetime.now()-timedelta(30), processed=True).order_by('-processed_date')
    return {
        'title': 'Trade History',
        'history': history,
    }


@secure
@login_required
@simple_view('members/history/rent.html')
def rent_history(request):
    history = RentOrder.objects.filter(user=request.user)
    return {
        'title': 'Rent History',
        'history': history,
    }


@login_required
@simple_view('members/buy/order_details.html')
def buy_order_details(request, id):
    pass


def _get_wizard(request, all_plans=False):
    """
    Returns wizard instance depending on user registration status
    """
    if request.user.is_authenticated():
        current_plan = MemberRentalPlan.get_current_plan(request.user)
        if current_plan:
            if current_plan.status in [RentalPlanStatus.CanceledP, RentalPlanStatus.Collection]:
                return redirect('members:rent_list')
            wizard = ChangeRentPlanWizard.create(request, all_plans=all_plans)
        else:
            wizard = MemberRentSignUpWizard.create(request)
    else:
        if not request.is_ajax():
            return redirect('catalog:index')
        wizard = NonMemberRentSignUpWizard.create(request)
    return wizard(request)


#@secure
def change_rent_plan(request):
    return _get_wizard(request)


def change_rent_plan2(request):
    if not request.is_ajax():
        return redirect('/')
    wizard = NonMemberRentSignUpWizard.create(request, initial={1: request.REQUEST})
    return wizard(request)


#@secure
@login_required
def rent_plan(request):
    return _get_wizard(request, all_plans=True)


@secure
@login_required
@simple_view('members/rent/cancel_membership.html')
def cancel_membership(request):
    current_plan = MemberRentalPlan.get_current_plan(request.user)
    if not current_plan:
        return redirect('members:change_rent_plan')

    if request.method == 'POST':
        if current_plan.status not in [RentalPlanStatus.Active, RentalPlanStatus.Delinquent, RentalPlanStatus.Pending, RentalPlanStatus.OnHold]:
            return redirect('members:cancel_membership')
        form = RentPlanCancellationForm(request.POST)
        if form.is_valid():
            reason = form.save()
            reason.user = request.user
            reason.plan = current_plan.plan
#            current_plan.send_cancel_request(reason)
            request.session['rent_cancellation_started'] = True
#            return redirect('members:cancel_membership_confirm_message')
            return cancel_membership_confirm(request, reason.confirmation_code)
    else:
        form = RentPlanCancellationForm()
    return {
        'rent_plan': MemberRentalPlan.get_current_plan(request.user),
        'form': form,
    }


@login_required
@simple_view('members/rent/cancel_membership_confirm_message.html')
def cancel_membership_confirm_message(request):
    if 'rent_cancellation_started' not in request.session:
        return redirect('members:cancel_membership')
    del request.session['rent_cancellation_started']


@login_required
#@transaction.commit_on_success
@simple_view('members/rent/cancel_membership_confirm.html')
def cancel_membership_confirm(request, code):
    plan = MemberRentalPlan.get_current_plan(request.user)
    if not plan:
        return redirect('members:rent_list')
#    if plan.cancel_confirmation_code != code or plan.cancel_confirmation_timestamp < datetime.now() - timedelta(2):
#        return redirect('members:cancel_membership')

    for r in CancellationReason.objects.filter(user=request.user, confirmation_code=code):
        r.is_confirmed = True
        r.save()

    for order in RentOrder.objects.filter(user=request.user, status=RentOrderStatus.Pending):
        order.status = RentOrderStatus.Canceled
        order.list_item = None
        order.save()

    orders = RentOrder.objects.filter(user=request.user, status__in=[RentOrderStatus.Prepared, RentOrderStatus.Shipped])
    if orders.count(): # Has games at home
        debug('Has games at home. Set status to be RentalPlanStatus.CanceledP')
        plan.status = RentalPlanStatus.CanceledP
        plan.cancellation_date = datetime.now()
        plan.cancel_confirmation_code = None
        plan.cancel_confirmation_timestamp = None
        plan.save()
    else:
        debug('Finish cancellation')
        plan.finish_cancellation()
        return redirect('members:rent_list')
    return {
        'plan': plan,
        'orders': orders,
    }


@login_required
@simple_view('members/lists/rent.html')
def rent_list(request):
    rent_plan = MemberRentalPlan.get_current_plan(request.user)
    rent_list = RentList.get(request=request)
    if request.user.is_authenticated():
        rent_orders = RentOrder.objects.filter(user=request.user).order_by('-id')
        rent_orders = rent_orders.filter(status__in=[RentOrderStatus.Pending, RentOrderStatus.Prepared, RentOrderStatus.Shipped])
        rent_orders = rent_orders.filter(list_item=None)
    else:
        rent_orders = None
    return {
        'buy_list': request.buy_list,
        'trade_list': TradeListItem.get(request),
        'rent_plan': rent_plan,
        'rent_list': rent_list,
        'rent_orders': rent_orders,
        'pending_credits': request.user.get_profile().get_pending_credits(),
        'banners': [ListPageBanner.objects.get_random()],
    }


@login_required
@simple_view('members/lists/buy.html')
def buy_list(request):
    if request.method == 'POST':
        # add to cart
        cart = BuyCart.get(request)
        for item in request.buy_list:
            if ('item-%d' % item.id) in request.POST:
                cart.push_item(request, item.item, inc_quantity=1, is_new=item.is_new)
                item.delete()
        return redirect(reverse('cart:index'))

    date_x = datetime.now() - timedelta(30)
    buy_orders = BuyOrder.objects.filter(user=request.user, create_date__gt=date_x).exclude(status=BuyOrderStatus.Canceled) if request.user.is_authenticated() else None

    return {
        'buy_list': request.buy_list,
        'buy_orders': buy_orders,
        'trade_list': TradeListItem.get(request),
        'rent_list': RentList.get(request=request),
        'pending_credits': request.user.get_profile().get_pending_credits(),
        'banners': [ListPageBanner.objects.get_random()],
    }


def buy_list_change(request, id):
    item = get_object_or_404(BuyList, id=id)
    if not request.is_ajax():
        return redirect(item.item.get_absolute_url())

    if request.method == 'POST':
        res = {}
        form = AddItemConditionForm(request.POST)
        if form.is_valid():
            item.is_new = form.cleaned_data['condition'] == 'new'
            item.save()
            res['redirect_to'] = reverse('members:buy_list')
        else:
            res['form'] = loader.render_to_string('cart/update.dialog.html',
                                                  {'form': form, 'item': item.item, 'list_item': item, },
                                                  RequestContext(request))
        return JsonResponse(res)

    form = AddItemConditionForm(initial={'condition': 'new' if item.is_new else 'used'})
    return render_to_response('cart/update.dialog.html',
                          {'form': form, 'item': item.item, 'list_item': item, },
                          context_instance=RequestContext(request))


@secure
@login_required
@simple_view('members/trade/store_credits.html')
def store_credits(request):
    profile = request.user.get_profile()
    credits = BillingHistory.get_store_gredits(request.user)
    return {
        'credits': credits,
        'total_store_credits': profile.unlocked_store_credits,
        'cashable_credits': profile.get_cashable_credits(),
    }

def address_lines(address_data):
    city = address_data.get('city') or ''
    county = address_data.get('county') or ''
    state = address_data.get('state') or ''
    zip_code = address_data.get('zip_code') or ''

    p1 = (city + ' ' + county).strip()
    p2 = (state + ' ' + zip_code).strip()
    if p1 and p2:
        address3 = p1 + ', ' + p2
    else:
        address3 = p1 + p2

    return [
        address_data.get('address1', ''),
        address_data.get('address2', ''),
        address3,
    ]


@secure
@login_required
@simple_view('members/trade/cash_back.html')
def cash_back(request):
    profile = request.user.get_profile()
    address = profile.get_shipping_address_data()

    errors = []

    if request.method == 'POST':
        form = CashOutOrderForm(request.POST)
        if form.is_valid():
            profile = request.user.get_profile()
            amount = form.cleaned_data['amount']
            if decimal.Decimal('0.7') * profile.get_cashable_credits() >= amount:
                if amount * decimal.Decimal(str(STORE_CREDIT_RATE)) < 25:
                    errors.append('Cash Out Credits must be minimum of $25.00')
                else:
                    order = CashOutOrder()
                    order.user = request.user
                    order.status = CashOutOrderStatus.Submitted
                    order.payment_method = form.cleaned_data['payment_method']
                    order.amount = amount

                    order.address1 = form.cached_address.get('address1')
                    order.address2 = form.cached_address.get('address2')
                    order.city = form.cached_address.get('city')
                    order.county = form.cached_address.get('county')
                    order.state = form.cached_address.get('state')
                    order.zip_code = form.cached_address.get('zip_code')

                    order.save()
                    return redirect('members:cash_back')
            else:
                errors.append('Cash Out Credits cannot exceed seventy percent (70%) of total cashable credit balance.')
    else:
        form = CashOutOrderForm(initial=address)

    requests_qs = CashOutOrder.objects.filter(user=request.user)

    for k, v in form.errors.iteritems():
        errors.append('%s: %s' % (k, ' '.join(v)))

    return {
        'store_credit_rate': STORE_CREDIT_RATE,
        'form': form,
        'errors': errors,
        'address_lines': address_lines(address),
        'pending_requests': requests_qs.filter(status=CashOutOrderStatus.Submitted).order_by('-submit_date'),
        'completed_requests': requests_qs.filter(status=CashOutOrderStatus.Processed).order_by('-process_date'),
    }


@secure
@login_required
def cash_back_delete(request, id):
    order = get_object_or_404(CashOutOrder, id=id, user=request.user, status=CashOutOrderStatus.Submitted)
    order.delete()
    return redirect('members:cash_back')


@secure
@login_required
@simple_view('members/account/terms_and_details.html')
def account_terms_and_details(request):
    plan = MemberRentalPlan.get_current_plan(request.user)

    if not plan or plan.status in [RentalPlanStatus.CanceledP, RentalPlanStatus.Collection]:
        return redirect('members:rent_list')

    allowed_games = '2' if plan.plan == RentalPlan.PlanA else 'unlimited'
    price_first_month, price_thereafter_months = RentalPlan.get_prices(plan.plan)
    return {
        'plan': plan,
        'plan_regular': plan.plan == RentalPlan.PlanA or plan.plan == RentalPlan.PlanB or plan.plan == RentalPlan.PlanC,
        'allowed_games': allowed_games,
        'price_first_month': price_first_month,
        'price_thereafter_months': price_thereafter_months,
        'membership_terms': RentalPlan.get_membership_terms(plan.plan) if plan else None,
    }


@login_required
@simple_view('members/account/personalize_your_games.html')
def personalize_your_games(request):
    if not request.is_ajax():
        return redirect('index')

    profile = request.user.get_profile()
    all_categories = Category.list()

    if request.method == 'POST':
        for s in all_categories:
            val = request.POST.get('system-%d' % s.id)
            if val:
                profile.owned_systems.add(s)
            else:
                profile.owned_systems.remove(s)

        for s in Genre.objects.all():
            val = request.POST.get('genre-%d' % s.id)
            if val:
                profile.favorite_genres.add(s)
            else:
                profile.favorite_genres.remove(s)
        try:
            parental_control = int(request.POST.get('parental_control'))
            if parental_control not in [0, 1, 2, 3, 4]: parental_control = 0
        except:
            parental_control = 0
        profile.parental_control = parental_control

        try:
            parental_control_reviews = int(request.POST.get('parental_control_reviews'))
            if parental_control_reviews not in [0, 1, 2]: parental_control_reviews = 0
        except:
            parental_control_reviews = 0
        profile.parental_control_reviews = parental_control_reviews

        profile.save()
        request.session['just_did_it'] = True
        return JsonResponse({'close': 'true'})

    owned_systems = profile.get_owned_systems()
    system_map = {}
    for s in all_categories:
        owned = False
        for os in owned_systems:
            if os.id == s.id:
                owned = True
        system_map[s.slug] = {'id': s.id, 'name': s.description, 'owned': owned}

    systems = [
        system_map['Xbox-Games'],
        system_map['Xbox-360-Games'],
        system_map['GameCube-Games'],
        system_map['Nintendo-DS-Games'],
        system_map['Nintendo-Wii-Games'],
        system_map['PlayStation-2-Games'],
        system_map['Sony-PSP-Games'],
        system_map['PlayStation-3-Games'],
    ]

    my_favorite_genres = profile.get_favorite_genres()
    favorite_genres = []
    for s in Genre.objects.all().order_by('name'):
        favorite = False
        for os in my_favorite_genres:
            if os.id == s.id:
                favorite = True
        favorite_genres.append({'id': s.id, 'name': s.name, 'favorite': favorite})

    return {
        'systems': systems,
        'genres': favorite_genres,
        'parental_control': profile.parental_control,
        'parental_control_reviews': profile.parental_control_reviews,
    }

@login_required
@simple_view('members/account/put_on_hold.html')
def account_put_on_hold(request):
    profile = request.user.get_profile()
    plan = MemberRentalPlan.get_current_plan(profile.user, exclude_canceled=True)
    if not plan or (plan.status != RentalPlanStatus.Active and plan.status != RentalPlanStatus.OnHold):
        return redirect('new_rent:change_plan')

    if request.method == 'POST':
        form = OnHoldForm(request.POST)
        if form.is_valid():
            plan.put_on_hold(form.cleaned_date())
            return redirect('members:put_on_hold')
    else:
        form = OnHoldForm()

    return {
        'fromdate': (datetime.now()+timedelta(days=7)).strftime('%B %d, %Y'),
        'todate': (datetime.now()+timedelta(days=30)).strftime('%B %d, %Y'),
        'form': form,
    }

@login_required
@simple_view('members/account/reactivate.html')
def account_reactivate(request):
    profile = request.user.get_profile()
    plan = MemberRentalPlan.get_current_plan(profile.user, exclude_canceled=True)
    if not plan or plan.status != RentalPlanStatus.OnHold:
        return redirect('new_rent:change_plan')

    if request.method == 'POST':
        plan.reactivate()
        return redirect('members:put_on_hold')

    return {}

@login_required
@simple_view('members/account/change_reactivation_date.html')
def account_change_reactivation_date(request):
    profile = request.user.get_profile()
    plan = MemberRentalPlan.get_current_plan(profile.user, exclude_canceled=True)
    if not plan or plan.status != RentalPlanStatus.OnHold:
        return redirect('new_rent:change_plan')

    if request.method == 'POST':
        form = OnHoldForm(request.POST)
        if form.is_valid():
            plan.put_on_hold(form.cleaned_date())
    else:
        form = OnHoldForm()

    return {
        'fromdate': (datetime.now()+timedelta(days=7)).strftime('%B %d, %Y'),
        'todate': (datetime.now()+timedelta(days=30)).strftime('%B %d, %Y'),
        'form': form,
    }
