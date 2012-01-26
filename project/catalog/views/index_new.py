import operator
from datetime import datetime, timedelta

from django.db.models.aggregates import Count
from django.db.models.query_utils import Q
from django.http import Http404
from django.core.paginator import Paginator
from django.shortcuts import redirect, get_object_or_404

from django_snippets.views.simple_view import simple_view
from django_snippets.utils.pagination import calc_paginator_ranges
from django_snippets.views.json_response import JsonResponse

from project.catalog.models.items import Item, RENT_STATUS_CHOICES,\
    ItemRentStatus
from project.catalog.models.ratings import Rating
from project.catalog.models.genres import Genre
from project.catalog.views.catalog import get_item_json_synopsis
from project.catalog.models.categories import Category
from project.banners.models import FeaturedGame
from project.offer_term.models import OfferTerm

def get_best_sellers(category):
    return Item.list_hottest_selling(category=category)


@simple_view('catalog/new/index.html')
def index_new(request, slug):
    current_category = None

    category = slug and get_object_or_404(Category, slug=slug)

    objects = Item.list_all(category=category).order_by('-release_date')

    all_games_count = objects.filter(release_date__lte=datetime.today()).count()

    current_filter = None
    applied_filters = 2

    if request.is_ajax():
        offer_msg_buy = ''
        offer_msg_trade = ''
        c = request.GET.get('c', '') or slug
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
            try:
                offer_msg_buy =  OfferTerm.objects.get(type=OfferTerm.BUY).text
            except:
                pass

        a = request.GET.get('a', '')
        if a:
            current_filter = 'rent'
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
            current_filter = 'trade'
            applied_filters += 1
            t = set(map(int, t.split(',')))
            if 100 in t:
                t.remove(100)
            if 200 in t:
                ff = [Q(hot_trade=True)]
                t.remove(200)
            else:
                ff = []
            if t:
                rr = [15, 25, 35]
                ff += map(lambda x: Q(trade_price__gte=rr[x], trade_flag=True, release_date__lte=datetime.now()), t)
            if ff:
                objects = objects.filter(reduce(operator.or_, ff))
            try:
                offer_msg_trade =  OfferTerm.objects.get(type=OfferTerm.TRADE).text
            except:
                pass

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
        elif current_filter != 'rent':
            objects = objects.filter(release_date__lte=datetime.today())
    else:
        objects = objects.filter(release_date__lte=datetime.today())
        if slug:
            current_category = get_object_or_404(Category, slug=slug)
            objects = objects.filter(category=current_category)

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

    if page != 'show all' or not request.is_ajax():
        paginator = Paginator(objects, 20, 4)
        try:
            if page == 'show all':
                page = 1
            current_page = paginator.page(page)
        except Exception, _e:
            raise Http404()
        objects = current_page.object_list
    else:
        paginator = None

    if request.is_ajax():
        items = []
        for o in objects:
            r = {'category': o.category.name, }
            if current_filter == 'rent':
                r['price'] = '%s' % o.get_rent_status_display()
            elif current_filter == 'trade':
                r['price'] = o.get_trade_value_display()
            else:
                r['price'] = ('$%s' % o.retail_price_new) if o.retail_price_new else '--'
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
            'offer_msg_trade':offer_msg_trade,
            'offer_msg_buy':offer_msg_buy,
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
                'show_all_link': applied_filters > 2 and paginator.num_pages > 1,
            })
        else:
            ctx['no_paginator'] = True
        return JsonResponse(ctx)
    else:
        all = Item.list_all(category=category).filter(release_date__lte=datetime.today())

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
        }, {
            'price': 200,
            'text': 'Hot Trade',
            'count': Item.list_all().filter(hot_trade=True).count(),
        },]
        RENT_STATUS_CHOICES_MAP = dict(RENT_STATUS_CHOICES)
        availability = []
        for a in (ItemRentStatus.Available, ItemRentStatus.High, ItemRentStatus.Medium, ItemRentStatus.Low, ItemRentStatus.Unknown, ItemRentStatus.NotReleased):
            availability.append({
                'id': a,
                'text': RENT_STATUS_CHOICES_MAP[a],
                'count': Item.list_all(category=category).filter(rent_status=a).count(),
            })
        availability.append({
            'id': 100,
            'text': 'Top Rental',
            'count': Item.list_all(category=category).filter(top_rental=True).count(),
        })

        esrb = Rating.objects.all().annotate(item_count=Count('item')).filter(item_count__gt=0).exclude(id=131126)


        all = Item.list_all(category=category).filter(retail_price_new__gt=0)
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
            'best_sellers': get_best_sellers(category),
            'genres': genres,
            'years': years,
            'prices': prices,
            'trade': trade,
            'availability': availability,
            'ratings': ratings,
            'esrb': esrb,
            'coming': coming,
            'all_games_count': all_games_count,
            'category': current_category,
            'featured_games': FeaturedGame.get(current_category, request),
        }
