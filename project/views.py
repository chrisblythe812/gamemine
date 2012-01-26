import operator
from logging import debug #@UnusedImport
from datetime import datetime, timedelta

from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext, Context
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Q
from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.aggregates import Count
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseBadRequest

from django_snippets.thirdparty.views.secure import secure
from django_snippets.views import simple_view, redirect_if_authenticated
from django_snippets.views.json_response import JsonResponse
from django_snippets.utils.pagination import calc_paginator_ranges

from project.catalog.models import Item
from project.catalog.models.categories import Category
from project.members.forms.signup import ProfileForm
from project.members.wizards import get_all_rental_plans_info

from project.members.models import HOW_DID_YOU_HEAR_CHOICES as HDYHC,\
    ProfileEntryPoint, Profile
from project.catalog.models.genres import Genre
from project.catalog.models.ratings import Rating
from project.catalog.views.catalog import get_item_json_synopsis
from project.catalog.models.items import ItemRentStatus, RENT_STATUS_CHOICES
from project.rent.models import RentList
from project.offer_term.models import OfferTerm
from datetime import timedelta

HOW_DID_YOU_HEAR_CHOICES = [('', 'Please Select')] + list(HDYHC)



DLP_CHOICES = {
    '/Buy/': ('buy','used','wholesale'),
    '/Trade/':('trade','swap',),
    '/Rent/':('rent',)
}

def get_slim_banner(request):
#    return {
#        'title': 'Deck the Halls',
#        'class': 'deck-the-halls',
#        'url': reverse('deck_the_halls'),
#    }
    return None


@redirect_if_authenticated('catalog:index')
@simple_view('index.html')
def index(request):
    referer = request.META.get('HTTP_REFERER', '').lower()
    if referer!='':
        for dlp in DLP_CHOICES:
            for s in DLP_CHOICES[dlp]:
                if referer.find(s)!=-1:
                    return redirect(dlp)
    items = Item.list_new_releases(None).exclude(rent_flag=False).order_by('?')[:30]
    return {
        'new_releases': items,
        'slim_banner': get_slim_banner(request),
    }


@redirect_if_authenticated('catalog:index')
@simple_view('intro/buy.html')
def buy_intro(request):
    qs = Item.list_all()
    date_x = datetime.now() - timedelta(30)
    filter = Q(release_date__lte=datetime.now()) & Q(release_date__gte=date_x) & Q(sold_amount__gt=0)
    qs = qs.filter(filter).order_by('-sold_amount', 'id')
    return {
        'new_releases': qs[:20],
        'slim_banner': get_slim_banner(request),
    }


@simple_view('intro/buy2.html')
def buy_intro2(request):
    objects = Item.list_all()
    objects = objects.filter(retail_price_new__gt=0).order_by('-release_date')

    all_games_count = objects.filter(release_date__lte=datetime.today()).count()

    applied_filters = 2

    if request.is_ajax():
        c = request.GET.get('c', '')
        if c:
            objects = objects.filter(category__slug=c)

        g = request.GET.get('g', '')
        if g:
            applied_filters += 1
            g = map(int, g.split(','))
            ff = map(lambda x: Q(genre_list__contains=Genre.objects.get(id=x).name), g)
            objects = objects.filter(reduce(operator.or_, ff))
        y = request.GET.get('y', '')
        if y:
            applied_filters += 1
            y = map(int, y.split(','))
            ff = map(lambda x: Q(release_date__year=x), y)
            objects = objects.filter(reduce(operator.or_, ff))
        r = request.GET.get('r', '')
        if r:
            applied_filters += 1
            r = map(int, r.split(','))
            ff = map(lambda x: Q(ratio__gte=x, ratio__lt=x+1), r)
            objects = objects.filter(reduce(operator.or_, ff))
        pr = request.GET.get('pr', '')
        if pr:
            applied_filters += 1
            rr = [('0.01', '20'), ('20', '50'), ('50', '10000')]
            pr = set(map(int, pr.split(',')))
            if 3 in pr:
                show_used = True
                pr.remove(3)
            else:
                show_used = False
            if pr:
                ff = map(lambda x: Q(retail_price_new__gte=rr[x][0], retail_price_new__lt=rr[x][1]) | Q(retail_price_used__gte=rr[x][0], retail_price_used__lt=rr[x][1]), pr)
                objects = objects.filter(reduce(operator.or_, ff))
            if show_used:
                objects = objects.filter(pre_owned=True)
        e = request.GET.get('e', '')
        if e:
            applied_filters += 1
            e = map(int, e.split(','))
            ff = map(lambda x: Q(rating=x), e)
            objects = objects.filter(reduce(operator.or_, ff))
        cs = request.GET.get('cs', '')
        if cs:
            applied_filters += 1
            cs = int(cs)
            today = datetime.today()
            if cs == 0:
                objects = objects.filter(release_date__gt=today)
            elif cs == 1:
                objects = objects.filter(release_date__gt=today, release_date__lte=today + timedelta(30))
            elif cs == 2:
                objects = objects.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60))
            objects = objects.order_by('release_date')
        else:
            objects = objects.filter(release_date__lte=datetime.today())
    else:
        objects = objects.filter(release_date__lte=datetime.today())

    if 'p' in request.GET:
        page = request.GET['p'].lower()
        if page != 'show all':
            try:
                page = int(page)
            except:
                return redirect(request.META['PATH_INFO'])
        elif applied_filters < 2:
            page = 1
    else:
        page = 1

    if page != 'show all':
        paginator = Paginator(objects, 16, 4)
        try:
            current_page = paginator.page(page)
        except Exception, _e:
            raise Http404()
        objects = current_page.object_list
    else:
        paginator = None

    if request.is_ajax():
        items = []
        for o in objects:
            r = {'category': o.category.name, 'price': ('$%s' % o.get_min_price()) if o.get_min_price() else '--', }
            r.update(get_item_json_synopsis(o))
            r['cover'] = o.get_cover()
            r['cover_w'] = 170
            r['cover_h'] = 220
            r['pre_owned'] = o.is_pre_owned()
            if o.is_pre_owned():
                r['actions']['buy'] += '?is_pre_owned=True'
            items.append(r)

        ctx = {
            'status': 'OK',
            'items': items,
        }
        if paginator:
            ctx.update({
                'show_paginator': True,
                'has_previous_page': current_page.has_previous(),
                'previous_page_number': current_page.previous_page_number(),
                'has_next_page': current_page.has_next(),
                'next_page_number' : current_page.next_page_number(),
                'page_number': page,
                'page_range': calc_paginator_ranges(paginator, page),
                'num_pages': paginator.num_pages,
            })
            if applied_filters > 2:
                ctx['show_all_link'] = True
        else:
            ctx['no_paginator'] = True
        return JsonResponse(ctx)
    else:
        all = Item.list_all().filter(retail_price_new__gt=0, release_date__lte=datetime.today())

        genres = Genre.objects.all().order_by('name')
        genres = map(lambda x: {'id': x.id, 'name': x.name, 'item_count': all.filter(genre_list__contains=x.name).count()}, genres)

        y = datetime.today().year
        years = map(lambda x: {'year': x, 'count': all.filter(release_date__year=x).count()}, range(y, y-3, -1))

        ratings = map(lambda x: {'rating': x, 'count': all.filter(Q(ratio__gte=x, ratio__lt=x+1)).count()}, [5, 4, 3])

        prices = [{
            'price': 0,
            'text': 'Under $20',
            'count': all.filter(retail_price_new__gt=0, retail_price_new__lt=20).count(),
        }, {
            'price': 1,
            'text': '$20 - $49.99',
            'count': all.filter(retail_price_new__gte=20, retail_price_new__lt=50).count(),
        }, {
            'price': 2,
            'text': 'Over $50',
            'count': all.filter(retail_price_new__gte=50).count(),
        }, {
            'price': 3,
            'text': 'Pre-Owned',
            'count': all.filter(pre_owned=True).count(),
        }]

        esrb = Rating.objects.all().annotate(item_count=Count('item')).filter(item_count__gt=0).exclude(id=131126)


        all = Item.list_all().filter(retail_price_new__gt=0)
        today = datetime.today()
        coming = [{
            'id': 0,
            'name': 'View All',
            'count': all.filter(release_date__gt=today).count(),
        }, {
            'id': 1,
            'name': 'This Month',
            'count': all.filter(release_date__gt=today, release_date__lte=today + timedelta(30)).count(),
        }, {
            'id': 2,
            'name': 'Next Month',
            'count': all.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60)).count(),
        }]

        """offer terms"""
        try:
            offer_msg =  OfferTerm.objects.get(type=OfferTerm.BUY).text
        except:
            offer_msg = None
        return {
            'page': current_page,
            'page_range': calc_paginator_ranges(paginator, page),
            'best_sellers': Item.list_hottest_selling(),
            'genres': genres,
            'years': years,
            'prices': prices,
            'ratings': ratings,
            'esrb': esrb,
            'coming': coming,
            'all_games_count': all_games_count,
            'offer_msg':offer_msg
        }


@simple_view('intro/rent2.html')
def rent_intro2(request):
#    if not settings.DEBUG and not request.META.get('HTTP_REFERER', None):
#        return redirect('rent_intro')

    qs = Item.list_all()
    qs = qs.filter(rent_amount__gt=0).order_by('-rent_amount', 'id')

    objects = Item.list_all()
    objects = objects.order_by('-release_date', '-top_rental')

    all_games_count = objects.count()

    applied_filters = 2

    if request.is_ajax():
        c = request.GET.get('c', '')
        if c:
            objects = objects.filter(category__slug=c)

        g = request.GET.get('g', '')
        if g:
            applied_filters += 1
            g = map(int, g.split(','))
            ff = map(lambda x: Q(genre_list__contains=Genre.objects.get(id=x).name), g)
            objects = objects.filter(reduce(operator.or_, ff))
        y = request.GET.get('y', '')
        if y:
            applied_filters += 1
            y = map(int, y.split(','))
            ff = map(lambda x: Q(release_date__year=x), y)
            objects = objects.filter(reduce(operator.or_, ff))
        r = request.GET.get('r', '')
        if r:
            applied_filters += 1
            r = map(int, r.split(','))
            ff = map(lambda x: Q(ratio__gte=x, ratio__lt=x+1), r)
            objects = objects.filter(reduce(operator.or_, ff))
        a = request.GET.get('a', '')
        if a:
            applied_filters += 1
            a = map(int, a.split(','))
            if 100 in a:
                ff = [Q(top_rental=True)]
            else:
                ff = []
            ff += map(lambda x: Q(rent_status=x), a)
            objects = objects.filter(reduce(operator.or_, ff))
            show_all = ItemRentStatus.NotReleased in a
        else:
            objects = objects.exclude(rent_status=ItemRentStatus.NotRentable)
            show_all = False
        e = request.GET.get('e', '')
        if e:
            applied_filters += 1
            e = map(int, e.split(','))
            ff = map(lambda x: Q(rating=x), e)
            objects = objects.filter(reduce(operator.or_, ff))
        cs = request.GET.get('cs', '')
        if cs:
            applied_filters += 1
            cs = int(cs)
            today = datetime.today()
            if cs == 0:
                objects = objects.filter(release_date__gt=today)
            elif cs == 1:
                objects = objects.filter(release_date__gt=today, release_date__lte=today + timedelta(30))
            elif cs == 2:
                objects = objects.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60))
            objects = objects.order_by('release_date', '-top_rental')
        elif not show_all:
            objects = objects.filter(release_date__lte=datetime.today())
    else:
        objects = objects.filter(rent_status__in=[ItemRentStatus.Available, ItemRentStatus.High, ItemRentStatus.Medium, ItemRentStatus.Low])

    if 'p' in request.GET:
        page = request.GET['p'].lower()
        if page != 'show all':
            try:
                page = int(page)
            except:
                return redirect(request.META['PATH_INFO'])
        elif applied_filters < 2:
            page = 1
    else:
        page = 1

    if page != 'show all':
        paginator = Paginator(objects, 16, 4)
        try:
            current_page = paginator.page(page)
        except Exception, _e:
            raise Http404()
        objects = current_page.object_list
    else:
        paginator = None

    if request.is_ajax():
        items = []
        for o in objects:
            r = {'category': o.category.name, 'rent_status': o.get_rent_status_display(), 'is_top_rental': o.is_top_rental(), }
            r.update(get_item_json_synopsis(o))
            r['cover'] = o.get_cover()
            r['cover_w'] = 170
            r['cover_h'] = 220
            r['pre_owned'] = o.is_pre_owned()
            items.append(r)

        ctx = {
            'status': 'OK',
            'items': items,
        }
        if paginator:
            ctx.update({
                'show_paginator': True,
                'has_previous_page': current_page.has_previous(),
                'previous_page_number': current_page.previous_page_number(),
                'has_next_page': current_page.has_next(),
                'next_page_number' : current_page.next_page_number(),
                'page_number': page,
                'page_range': calc_paginator_ranges(paginator, page),
                'num_pages': paginator.num_pages,
            })
            if applied_filters > 2:
                ctx['show_all_link'] = True
        else:
            ctx['no_paginator'] = True
        return JsonResponse(ctx)
    else:
        all = Item.list_all().exclude(rent_status=ItemRentStatus.NotRentable)

        genres = Genre.objects.all().order_by('name')
        genres = map(lambda x: {'id': x.id, 'name': x.name, 'item_count': all.filter(genre_list__contains=x.name).count()}, genres)

        y = datetime.today().year
        years = map(lambda x: {'year': x, 'count': all.filter(release_date__year=x).count()}, range(y, y-3, -1))

        ratings = map(lambda x: {'rating': x, 'count': all.filter(Q(ratio__gte=x, ratio__lt=x+1)).count()}, [5, 4, 3])

        RENT_STATUS_CHOICES_MAP = dict(RENT_STATUS_CHOICES)
        availability = []
        for a in (ItemRentStatus.Available, ItemRentStatus.High, ItemRentStatus.Medium, ItemRentStatus.Low, ItemRentStatus.Unknown, ItemRentStatus.NotReleased):
            availability.append({
                'id': a,
                'text': RENT_STATUS_CHOICES_MAP[a],
                'count': all.filter(rent_status=a).count(),
            })
        availability.append({
            'id': 100,
            'text': 'Top Rental',
            'count': Item.list_all().filter(top_rental=True).count(),
        })

        esrb = Rating.objects.all().annotate(item_count=Count('item')).filter(item_count__gt=0).exclude(id=131126)


        all = Item.list_all().filter(retail_price_new__gt=0)
        today = datetime.today()
        coming = [{
            'id': 0,
            'name': 'View All',
            'count': all.filter(release_date__gt=today).count(),
        }, {
            'id': 1,
            'name': 'This Month',
            'count': all.filter(release_date__gt=today, release_date__lte=today + timedelta(30)).count(),
        }, {
            'id': 2,
            'name': 'Next Month',
            'count': all.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60)).count(),
        }]

        return {
            'page': current_page,
            'page_range': calc_paginator_ranges(paginator, page),
            'top_rentals': qs[:20],
            'genres': genres,
            'years': years,
            'availability': availability,
            'ratings': ratings,
            'esrb': esrb,
            'coming': coming,
            'all_games_count': all_games_count,
        }


@redirect_if_authenticated('catalog:index')
@simple_view('intro/trade.html')
def trade_intro(request):
    qs = Item.list_all()
    date_x = datetime.now() - timedelta(30)
    filter = Q(trade_flag=True) & Q(release_date__lte=datetime.now()) & Q(release_date__gte=date_x)
    qs = qs.filter(filter).order_by('-trade_price', 'id')
    return {
        'new_releases': qs[:20],
        'slim_banner': get_slim_banner(request),
    }


@simple_view('intro/trade2.html')
def trade_intro2(request):
    qs = Item.list_all().filter(trade_flag=True, trade_amount__gt=0, trade_price__gt=0)
    hot_trades = qs.order_by('-trade_amount', 'id')[:20]

    objects = Item.list_all()
    objects = objects.order_by('-release_date', '-hot_trade')

    all_games_count = objects.count()

    applied_filters = 2

    if request.is_ajax():
        c = request.GET.get('c', '')
        if c:
            objects = objects.filter(category__slug=c)

        g = request.GET.get('g', '')
        if g:
            applied_filters += 1
            g = map(int, g.split(','))
            ff = map(lambda x: Q(genre_list__contains=Genre.objects.get(id=x).name), g)
            objects = objects.filter(reduce(operator.or_, ff))
        y = request.GET.get('y', '')
        if y:
            applied_filters += 1
            y = map(int, y.split(','))
            ff = map(lambda x: Q(release_date__year=x), y)
            objects = objects.filter(reduce(operator.or_, ff))
        r = request.GET.get('r', '')
        if r:
            applied_filters += 1
            r = map(int, r.split(','))
            ff = map(lambda x: Q(ratio__gte=x, ratio__lt=x+1), r)
            objects = objects.filter(reduce(operator.or_, ff))
        t = request.GET.get('t', '')
        if t:
            vv = [15, 25, 35]
            applied_filters += 1
            t = set(map(int, t.split(',')))
            if 200 in t:
                ff = [Q(hot_trade=True)]
                t.remove(200)
            else:
                ff = []
            ff += map(lambda x: Q(trade_price__gte=vv[x]), t)
            objects = objects.filter(reduce(operator.or_, ff))
        e = request.GET.get('e', '')
        if e:
            applied_filters += 1
            e = map(int, e.split(','))
            ff = map(lambda x: Q(rating=x), e)
            objects = objects.filter(reduce(operator.or_, ff))
        cs = request.GET.get('cs', '')
        if cs:
            applied_filters += 1
            cs = int(cs)
            today = datetime.today()
            if cs == 0:
                objects = objects.filter(release_date__gt=today)
            elif cs == 1:
                objects = objects.filter(release_date__gt=today, release_date__lte=today + timedelta(30))
            elif cs == 2:
                objects = objects.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60))
            objects = objects.order_by('release_date', '-hot_trade')
        else:
            objects = objects.filter(trade_price__gt=0, trade_flag=True, release_date__lte=datetime.now())
    else:
        objects = objects.filter(trade_price__gt=0, trade_flag=True, release_date__lte=datetime.now())

    if 'p' in request.GET:
        page = request.GET['p'].lower()
        if page != 'show all':
            try:
                page = int(page)
            except:
                return redirect(request.META['PATH_INFO'])
        elif applied_filters < 2:
            page = 1
    else:
        page = 1

    if page != 'show all':
        paginator = Paginator(objects, 16, 4)
        try:
            current_page = paginator.page(page)
        except Exception, _e:
            raise Http404()
        objects = current_page.object_list
    else:
        paginator = None

    if request.is_ajax():
        items = []
        for o in objects:
            r = {'category': o.category.name, 'trade_value': o.get_trade_value_display(), 'is_hot_trade': o.hot_trade, }
            r.update(get_item_json_synopsis(o))
            r['cover'] = o.get_cover()
            r['cover_w'] = 170
            r['cover_h'] = 220
            r['hot_trade'] = o.hot_trade
            items.append(r)

        ctx = {
            'status': 'OK',
            'items': items,
        }
        if paginator:
            ctx.update({
                'show_paginator': True,
                'has_previous_page': current_page.has_previous(),
                'previous_page_number': current_page.previous_page_number(),
                'has_next_page': current_page.has_next(),
                'next_page_number' : current_page.next_page_number(),
                'page_number': page,
                'page_range': calc_paginator_ranges(paginator, page),
                'num_pages': paginator.num_pages,
            })
            if applied_filters > 2:
                ctx['show_all_link'] = True
        else:
            ctx['no_paginator'] = True
        return JsonResponse(ctx)
    else:
        all = Item.list_all().filter(trade_price__gt=0, trade_flag=True, release_date__lte=datetime.now())

        genres = Genre.objects.all().order_by('name')
        genres = map(lambda x: {'id': x.id, 'name': x.name, 'item_count': all.filter(genre_list__contains=x.name).count()}, genres)

        y = datetime.today().year
        years = map(lambda x: {'year': x, 'count': all.filter(release_date__year=x).count()}, range(y, y-3, -1))

        ratings = map(lambda x: {'rating': x, 'count': all.filter(Q(ratio__gte=x, ratio__lt=x+1)).count()}, [5, 4, 3])

        trade = []
        for a in range(3):
            p = (15, 25, 35)[a]
            trade.append({
                'id': a,
                'text': 'Over $%s' % p,
                'count': all.filter(trade_price__gte=p).count(),
            })
        trade.append({
            'id': 200,
            'text': 'Hot Trade',
            'count': Item.list_all().filter(hot_trade=True).count(),
        })

        esrb = Rating.objects.all().annotate(item_count=Count('item')).filter(item_count__gt=0).exclude(id=131126)


        all = Item.list_all()
        today = datetime.today()
        coming = [{
            'id': 0,
            'name': 'View All',
            'count': all.filter(release_date__gt=today).count(),
        }, {
            'id': 1,
            'name': 'This Month',
            'count': all.filter(release_date__gt=today, release_date__lte=today + timedelta(30)).count(),
        }, {
            'id': 2,
            'name': 'Next Month',
            'count': all.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60)).count(),
        }]

        """offer terms"""
        try:
            offer_msg = OfferTerm.objects.get(type=OfferTerm.TRADE).text
        except:
            offer_msg = None

        return {
            'page': current_page,
            'page_range': calc_paginator_ranges(paginator, page),
            'hot_trades': hot_trades,
            'genres': genres,
            'years': years,
            'trade': trade,
            'ratings': ratings,
            'esrb': esrb,
            'coming': coming,
            'all_games_count': all_games_count,
            'offer_msg' : offer_msg,
        }


@redirect_if_authenticated('catalog:index')
def rent_intro(request):
    class Form(forms.Form):
        email = forms.EmailField(widget=forms.TextInput(attrs={'tabindex': '1'}))
        confirm_email = forms.EmailField(widget=forms.TextInput(attrs={'tabindex': '2'}))
        password = forms.CharField(widget=forms.PasswordInput(attrs={'tabindex': '3'}))
        confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'tabindex': '4'}))
        username = forms.CharField(widget=forms.TextInput(attrs={'tabindex': '5'}))
        how_did_you_hear = forms.ChoiceField(choices=HOW_DID_YOU_HEAR_CHOICES, widget=forms.Select(attrs={'tabindex': '6'}))


    qs = Item.list_all()
    date_x = datetime.now() - timedelta(30)
    filter = Q(rent_flag=True) & Q(release_date__lte=datetime.now()) & Q(release_date__gte=date_x) & Q(rent_amount__gt=0)
    qs = qs.filter(filter).order_by('-rent_amount', 'id')
    context = {
        'new_releases': qs[:20],
#        'slim_banner': get_slim_banner(request),
        'form': Form(),
    }
    all_plans = get_all_rental_plans_info(request)[:2]
    page_id = int(request.GET.get('pageid',0))
    if page_id == 0:
        template = 'intro/rent.html'
        all_plans = get_all_rental_plans_info(request)
    elif page_id == 1:
        template = 'intro/landing-1.html'
        qs = Item.list_all()
        qs_base = qs.filter(rent_amount__gt=0).order_by('-rent_amount', 'id')
        qs = qs_base
        rent_list = RentList.objects.filter(rent_order__date_rent__gte=datetime.now() - timedelta(days=7)).values('item__id').query
        qs = qs.filter(id__in=rent_list)
        if qs.count() < 3:
            qs = qs_base
        context['qs'] = qs[:7]
    elif page_id == 2:
        template = 'intro/landing-2.html'
    else:
        template = 'intro/landing-3.html'
    context['all_plans'] = all_plans
    return render_to_response(template,
                              context,
                              context_instance=RequestContext(request))


#@cache_page(60*60*24*7)
def simple_page(request, page):
    template = 'simple_pages/%s.html' % page.lower()
    context = {
        'What-is-My-Game-Worth': {
            'categories': [
                Category.objects.get(slug='Xbox-360-Games'),
                Category.objects.get(slug='Nintendo-Wii-Games'),
                Category.objects.get(slug='Nintendo-DS-Games'),
                Category.objects.get(slug='PlayStation-3-Games'),
                Category.objects.get(slug='PlayStation-2-Games'),
                Category.objects.get(slug='Sony-PSP-Games'),
                Category.objects.get(slug='Xbox-Games'),
                Category.objects.get(slug='GameCube-Games'),
            ],
        },
        'Seals': {
            'bg_type': request.GET.get('t'),
        }
    }.get(page, {})
    return render_to_response(template,
                              context,
                              context_instance=RequestContext(request))

@secure
def seals(request, t=None):
    template = 'simple_pages/seals.html'
    context = {
       'bg_type': t or request.GET.get('t'),
    }
    return render_to_response(template,
                              context,
                              context_instance=RequestContext(request))

class DeckTheHallsRegisterForm(ProfileForm):
    first_name = forms.CharField(label='First Name', widget=forms.TextInput(attrs={'tabindex': '1'}),
                                 error_messages={'required': 'First name is required. Please review the form and continue.'})
    last_name = forms.CharField(label='Last Name', widget=forms.TextInput(attrs={'tabindex': '2'}),
                                error_messages={'required': 'Last name is required. Please review the form and continue.'})
    email = forms.EmailField(label='Email Address', widget=forms.TextInput(attrs={'tabindex': '3'}),
                             error_messages={'required': 'Email address is required. Please review the form and continue.'})
    confirm_email = forms.EmailField(label='Confirm Email Address', widget=forms.TextInput(attrs={'tabindex': '4'}),
                                     error_messages={'required': 'Email address confirmation FAILED.'})
    password = forms.CharField(max_length=16, min_length=6, widget=forms.PasswordInput(attrs={'tabindex': '5'}), label='Create a Password',
                               error_messages={'required': 'Password is required. Please review the form and continue.'})
    confirm_password = forms.CharField(max_length=16, min_length=6, widget=forms.PasswordInput(attrs={'tabindex': '6'}), label='Confirm Password',
                                       error_messages={'required': 'Password confirmation FAILED. Please review the form and continue.'})
    username = forms.CharField(label='Username/Profile ID', widget=forms.TextInput(attrs={'tabindex': '7'}),
                               error_messages={'required': 'Username is required. Please review the form and continue.'})
    how_did_you_hear = forms.ChoiceField(choices=HOW_DID_YOU_HEAR_CHOICES, required=True, label='How did you hear about us?',
                                         widget=forms.Select(attrs={'tabindex': '8'}),
                                         error_messages={'required': 'Please tell how did you hear about us.'})

    def clean_confirm_email(self):
        data = self.cleaned_data
        email = data.get('email')
        confirm_email = data.get('confirm_email')
        if email != confirm_email:
            raise forms.ValidationError('Email Confirmation FAILED!')
        return confirm_email


    @transaction.commit_on_success
    def save(self, request, entry_point=ProfileEntryPoint.DeckTheHalls):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        username = self.cleaned_data.get('username')
        if settings.MELISSA:
            full_name = self.cleaned_data.get('first_name') + ' ' + self.cleaned_data.get('last_name')
            full_name = settings.MELISSA.inaccurate_name(full_name=full_name)
            first_name = full_name['first_name']
            last_name = full_name['last_name']
        else:
            first_name = self.cleaned_data.get('first_name')
            last_name = self.cleaned_data.get('last_name')
        u = User(username=username,
                 email=email,
                 is_active=False,
                 first_name=first_name,
                 last_name=last_name)
        u.set_password(password)
        u.save()
        p = Profile.create(request, u, entry_point=entry_point)
        p.save()
        p.send_email_confirmation_mail()
        return u


@redirect_if_authenticated('catalog:index')
@simple_view('deck_the_halls.html')
def deck_the_halls(request):
    error = None
    if request.method == 'POST':
        form = DeckTheHallsRegisterForm(request.POST)
        if form.is_valid():
            form.save(request)
            if request.is_ajax():
                return JsonResponse({'redirect_to': reverse('members:create_account_complete')})
            else:
                return redirect('members:create_account_complete')

        def get_error(form):
            for n, _f in form.fields.items():
                if form.errors.get(n):
                    return form.errors[n][0]
            e = form.errors.get('__all__')
            if e:
                return e[0]
            return 'Error'
        error = get_error(form)
        if request.is_ajax():
            return JsonResponse({'error': error})
    else:
        form = DeckTheHallsRegisterForm()
    return {
        'form': form,
        'error': error,
    }


@simple_view('maintenance.html')
def maintenance(request):
    pass


@simple_view('500.html')
def page500(request):
    pass


def oups(request):
    from project.rent.models import MemberRentalPlan
    ctx = {
        'CATALOG_CATEGORIES': Category.list_names(),
        'SITE_URL': 'http://%s' % Site.objects.get_current().domain,
        'STATIC_URL': settings.STATIC_URL,
    }

#    plan = MemberRentalPlan.get_current_plan(request.user)
    plan = MemberRentalPlan.objects.all()[0]

    from project.utils.mailer import mail
    mail('roman@bravetstudio.com', 'emails/rent_emails/plan_subscription_successfull.html', {
        'user': plan.user,
        'plan': plan,
        'new_releases': Item.list_new_releases(6),
        'coming_soon': Item.list_all()[:6],
    }, subject="TEST EMAIL!")

    return render_to_response('emails/rent_emails/plan_subscription_successfull.html', {
        'user': plan.user,
        'plan': plan,
        'new_releases': Item.list_new_releases(6),
        'coming_soon': Item.list_all()[:6],
    }, Context(ctx))


def campaign(request):
#    debug(request.campaign_id)
    return redirect('index')


def get_wimgw_context(request, ctx={}):
    res = {
        'categories': [
            Category.objects.get(slug='Xbox-360-Games'),
            Category.objects.get(slug='Nintendo-Wii-Games'),
            Category.objects.get(slug='Nintendo-DS-Games'),
            Category.objects.get(slug='PlayStation-3-Games'),
            Category.objects.get(slug='PlayStation-2-Games'),
            Category.objects.get(slug='Sony-PSP-Games'),
            Category.objects.get(slug='Xbox-Games'),
            Category.objects.get(slug='GameCube-Games'),
        ],}
    res.update(ctx)
    return res

def get_default_filter_context(request, ctx={}):
    all = Item.list_all().filter(release_date__lte=datetime.today())
    all_games_count = all.filter(release_date__lte=datetime.today()).count()

    genres = Genre.objects.all().order_by('name')
    genres = map(lambda x: {'id': x.id, 'name': x.name, 'item_count': all.filter(genre_list__contains=x.name).count()}, genres)

    y = datetime.today().year
    years = map(lambda x: {'year': x, 'count': all.filter(release_date__year=x).count()}, range(y, y-3, -1))

    ratings = map(lambda x: {'rating': x, 'count': all.filter(Q(ratio__gte=x, ratio__lt=x+1)).count()}, [5, 4, 3])

    prices = [{
        'price': 0,
        'text': 'Under $20',
        'count': all.filter(retail_price_new__gt=0, retail_price_new__lt=20).count(),
    }, {
        'price': 1,
        'text': '$20 - $49.99',
        'count': all.filter(retail_price_new__gte=20, retail_price_new__lt=50).count(),
    }, {
        'price': 2,
        'text': 'Over $50',
        'count': all.filter(retail_price_new__gte=50).count(),
    }, {
        'price': 3,
        'text': 'Pre-Owned',
        'count': all.filter(pre_owned=True).count(),
    }]

    RENT_STATUS_CHOICES_MAP = dict(RENT_STATUS_CHOICES)
    availability = []
    for a in (ItemRentStatus.Available, ItemRentStatus.High, ItemRentStatus.Medium, ItemRentStatus.Low, ItemRentStatus.Unknown, ItemRentStatus.NotReleased):
        availability.append({
            'id': a,
            'text': RENT_STATUS_CHOICES_MAP[a],
            'count': Item.list_all().filter(rent_status=a).count(),
        })
    availability.append({
        'id': 100,
        'text': 'Top Rental',
        'count': Item.list_all().filter(top_rental=True).count(),
    })

    trade = [{
        'price': 0,
        'text': 'Over $15',
        'count': all.filter(trade_price__gte=15).count(),
    }, {
        'price': 1,
        'text': 'Over $25',
        'count': all.filter(trade_price__gte=25).count(),
    }, {
        'price': 2,
        'text': 'Over $35',
        'count': all.filter(trade_price__gte=35).count(),
    },]

    esrb = Rating.objects.all().annotate(item_count=Count('item')).filter(item_count__gt=0).exclude(id=131126)

    all = Item.list_all().filter(retail_price_new__gt=0)
    today = datetime.today()
    coming = [{
        'id': 0,
        'name': 'View All',
        'count': all.filter(release_date__gt=today).count(),
    }, {
        'id': 1,
        'name': 'This Month',
        'count': all.filter(release_date__gt=today, release_date__lte=today + timedelta(30)).count(),
    }, {
        'id': 2,
        'name': 'Next Month',
        'count': all.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60)).count(),
    }]

    res = {
        'genres': genres,
        'years': years,
        'prices': prices,
        'ratings': ratings,
        'availability': availability,
        'trade': trade,
        'esrb': esrb,
        'coming': coming,
        'all_games_count': all_games_count,
        'b': Item.objects.filter(pk__in=[800008, 800013, 800002])
    }
    res.update(get_wimgw_context(request))
    res.update(ctx)
    return res


@simple_view('wimgw.html')
def wimgw(request):
    if request.is_ajax():
        if 'wimgw' in request.GET:
            return render_to_response('partials/wimgw.html', get_wimgw_context(request), RequestContext(request))
        elif 'carousel' in request.GET:
            carousel = request.GET['carousel']
            if carousel not in ['rent', 'trade', 'buy']:
                return HttpResponseBadRequest()
            if 'c' in request.GET:
                category = get_object_or_404(Category, slug=request.GET['c'])
            else:
                category = None
            carousel = {
                'trade': ('hottest_tradeins_carousel', {
                    'hot_trades': Item.list_all(category=category).filter(trade_flag=True, trade_price__gt=0).order_by('-trade_amount', 'id')[:20],}),
                'rent': ('most_rentals_carousel', {
                    'most_rentals': Item.list_all(category=category).filter(rent_flag=True).order_by('-rent_amount', 'id')[:20],}),
                'buy': ('best_sellers_carousel', {
                    'best_sellers': Item.list_hottest_selling(category=category)}),
            }[carousel]
            return render_to_response('partials/wimgw/%s.html' % carousel[0],
                                      carousel[1], RequestContext(request))

    q = None
    current_category = None
    objects = Item.list_all()
    applied_filters = 2
    if request.is_ajax():
        if 'q' in request.GET:
            q = request.GET['q']
            objects = Item.search_by_keyword(q).filter(trade_flag=True, trade_price__gt=0)

        c = request.GET.get('c', '')
        if c:
            objects = objects.filter(category__slug=c)
            current_category = Category.objects.get(slug=c)

        g = request.GET.get('g', '')
        if g:
            applied_filters += 1
            g = map(int, g.split(','))
            ff = map(lambda x: Q(genre_list__contains=Genre.objects.get(id=x).name), g)
            objects = objects.filter(reduce(operator.or_, ff))
        y = request.GET.get('y', '')
        if y:
            applied_filters += 1
            y = map(int, y.split(','))
            ff = map(lambda x: Q(release_date__year=x), y)
            objects = objects.filter(reduce(operator.or_, ff))
        r = request.GET.get('r', '')
        if r:
            applied_filters += 1
            r = map(int, r.split(','))
            ff = map(lambda x: Q(ratio__gte=x, ratio__lt=x+1), r)
            objects = objects.filter(reduce(operator.or_, ff))
        pr = request.GET.get('pr', '')
        if pr:
            applied_filters += 1
            rr = [('0.01', '20'), ('20', '50'), ('50', '10000')]
            pr = set(map(int, pr.split(',')))
            if 3 in pr:
                show_used = True
                pr.remove(3)
            else:
                show_used = False
            if pr:
                ff = map(lambda x: Q(retail_price_new__gte=rr[x][0], retail_price_new__lt=rr[x][1]) | Q(retail_price_used__gte=rr[x][0], retail_price_used__lt=rr[x][1]), pr)
                objects = objects.filter(reduce(operator.or_, ff))
            if show_used:
                objects = objects.filter(pre_owned=True)
        a = request.GET.get('a', '')
        if a:
            applied_filters += 1
            a = map(int, a.split(','))
            if 100 in a:
                ff = [Q(top_rental=True)]
            else:
                ff = []
            ff += map(lambda x: Q(rent_status=x), a)
            objects = objects.filter(reduce(operator.or_, ff))
        else:
            objects = objects.exclude(rent_status=ItemRentStatus.NotRentable)
        t = request.GET.get('t', '')
        if t:
            applied_filters += 1
            rr = [15, 25, 35]
            t = set(map(int, t.split(',')))
            if 100 in t:
                wimgw = True
                t.remove(100)
            else:
                wimgw = False
            if t:
                ff = map(lambda x: Q(trade_price__gte=rr[x], trade_flag=True, release_date__lte=datetime.now()), t)
                objects = objects.filter(reduce(operator.or_, ff))
        e = request.GET.get('e', '')
        if e:
            applied_filters += 1
            e = map(int, e.split(','))
            ff = map(lambda x: Q(rating=x), e)
            objects = objects.filter(reduce(operator.or_, ff))
        cs = request.GET.get('cs', '')
        if cs:
            applied_filters += 1
            cs = int(cs)
            today = datetime.today()
            if cs == 0:
                objects = objects.filter(release_date__gt=today)
            elif cs == 1:
                objects = objects.filter(release_date__gt=today, release_date__lte=today + timedelta(30))
            elif cs == 2:
                objects = objects.filter(release_date__gt=today + timedelta(30), release_date__lte=today + timedelta(60))
            objects = objects.order_by('release_date')


    if 'p' in request.GET:
        page = request.GET['p'].lower()
        if page != 'show all':
            try:
                page = int(page)
            except:
                return redirect(request.META['PATH_INFO'])
        elif applied_filters < 2:
            page = 1
    else:
        page = 1

    items_found = objects.count()

    if page != 'show all':
        paginator = Paginator(objects, 16, 4)
        try:
            current_page = paginator.page(page)
        except Exception, _e:
            raise Http404()
        objects = current_page.object_list
    else:
        paginator = None

    if request.is_ajax():
        if paginator:
            paginator_ctx = {
                'show_paginator': True,
                'has_previous_page': current_page.has_previous(),
                'previous_page_number': current_page.previous_page_number(),
                'has_next_page': current_page.has_next(),
                'next_page_number' : current_page.next_page_number(),
                'page_number': page,
                'page_range': calc_paginator_ranges(paginator, page),
                'num_pages': paginator.num_pages,
                'show_all_link': applied_filters > 2 and paginator.num_pages > 1,
            }
        else:
            paginator_ctx = {'no_paginator': True,}

        if q is not None:
            ctx = {
                'q': q,
                'items': objects,
                'current_category': current_category,
                'items_found': items_found,
            }
            ctx.update(paginator_ctx)
            return render_to_response('partials/wimgw_search_results.html', get_wimgw_context(request, ctx), RequestContext(request))

        items = []
        for o in objects:
            r = {'category': o.category.name, 'price': ('$%s' % o.get_min_price()) if o.get_min_price() else '--', }
            r.update(get_item_json_synopsis(o))
            r['cover'] = o.get_cover()
            r['cover_w'] = 170
            r['cover_h'] = 220
            r['pre_owned'] = o.is_pre_owned()
            if o.is_pre_owned():
                r['actions']['buy'] += '?is_pre_owned=True'
            items.append(r)

        ctx = {
            'status': 'OK',
            'items': items,
        }
        ctx.update(paginator_ctx)
        return JsonResponse(ctx)
    else:
        return get_default_filter_context(request, {
                'best_sellers': Item.list_hottest_selling(),
            })
