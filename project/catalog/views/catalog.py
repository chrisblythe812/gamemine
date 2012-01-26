from logging import debug #@UnusedImport
import random
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404
from django.core.urlresolvers import reverse
from django.db.models import Q

from django_snippets.views import simple_view, JsonResponse
from django_snippets.utils.pagination import calc_paginator_ranges

from project.catalog.models import Category, Genre, Item
from project.banners.models import FeaturedGame


CATALOG_FILTERS = (
    ('new-releases', 'New Releases'),
    ('best-sellers', 'Best Sellers'),
    ('top-trades', 'Top Trades'),
    ('top-rentals', 'Top Rentals'),
    ('coming-soon', 'Coming Soon'),
)


def get_item_json_synopsis(o):
    data = {
        'id': o.id,
        'short_name': o.get_cropped_name(),
        'name': unicode(o),
        'url': o.get_absolute_url(),
        'actions': {},
        'cover': o.get_catalog_grid_cover(),
        'thumb_image': o.get_thumb_image(),
    }
    data['actions']['buy'] = reverse('cart:add', args=[o.id])
    data['actions']['rent'] = reverse('rent:add', args=[o.id])
    data['actions']['trade'] = reverse('trade:add', args=[o.id])
    return data


def quick_game_finder(qs, q):
    qs = Item.search_by_keyword(q, qs)
    return qs


@simple_view('catalog/category.html')
def category(request, slug, filter):
    category = slug and get_object_or_404(Category, slug=slug)

    if 'genre' in request.GET:
        genre = request.GET.get('genre', '*')
        try:
            request.session['filter/genre'] = Genre.objects.get(pk=int(genre))
        except:
            request.session['filter/genre'] = None
        return redirect(request.META['PATH_INFO'])
    
    if 'p' in request.GET:
        try:
            page = int(request.GET['p'])
        except:
            return redirect(request.META['PATH_INFO'])
    else:
        page = 1
    genres = category.list_genres() if category else Genre.objects.all()[:]
    genre = request.session.get('filter/genre')
    if genre and (genre not in genres):
        genre = None

    # TODO: resolve me!    
    genres = genres[:15]

    auto_filter = False if filter else True
    filter = (filter, dict(CATALOG_FILTERS).get(filter)) if filter else CATALOG_FILTERS[0]
    
    featured_games = FeaturedGame.get(category, request)
#    if category:
#        featured_games = FeaturedGame.get(category)
#    else:
#        featured_games = CatalogBanner.get()
    
    if category: 
        objects = Item.list_by_category(category, genre)
    else:
        objects = Item.list_all(genre)

    q = request.GET.get('q')
    if q:
        objects = quick_game_finder(objects, q)
    else:
        def get_objects(*args, **kwargs):
            filter = kwargs.get('filter')
            if category or not request.user.is_authenticated():
                qs = objects.order_by(*args)
                if filter:
                    qs = qs.filter(filter)
                return qs
            else:
                own_consoles = request.user.get_profile().get_owned_systems()
                o1 = objects.filter(category__in=own_consoles).order_by(*args)
                if filter: o1 = o1.filter(filter)
                o2 = objects.exclude(category__in=own_consoles).order_by(*args)
                if filter: o2 = o2.filter(filter)
                return list(o1) + list(o2)
                
        
        f = filter and filter[0]
        if f == 'best-sellers':
            date_x = datetime.now() - timedelta(60)
            filter = Q(release_date__lte=datetime.now()) & Q(release_date__gte=date_x) & Q(sold_amount__gt=0)
            objects = get_objects('-sold_amount', '-release_date', 'id', filter=filter)
        elif f == 'top-rentals':
            date_x = datetime.now() - timedelta(60)
            filter = Q(rent_flag=True) & Q(release_date__lte=datetime.now()) & Q(release_date__gte=date_x) & Q(rent_amount__gt=0)
            objects = get_objects('-rent_amount', '-release_date', 'id', filter=filter)
        elif f == 'top-trades':
#            date_x = datetime.now() - timedelta(60)
#            filter = Q(trade_flag=True) & Q(release_date__lte=datetime.now()) & Q(release_date__gte=date_x) & Q(trade_amount__gt=0)
            filter = Q(trade_flag=True) & Q(release_date__lte=datetime.now()) & Q(trade_amount__gt=0)
            objects = get_objects('-trade_amount', '-release_date', 'id', filter=filter)
        elif f == 'new-releases':
            date_x = datetime.now() - timedelta(60)
            objects = objects.filter(release_date__gt=date_x, release_date__lte=datetime.now()).order_by('-release_date')
            if not category and request.user.is_authenticated():
                objects = objects.filter(release_date__gt=date_x, release_date__lte=datetime.now())
                own_consoles = request.user.get_profile().get_owned_systems()
                o1 = objects.filter(category__in=own_consoles)
                o2 = objects.exclude(category__in=own_consoles)
                objects = list(o1) + list(o2)
        else:
            seed = request.session.get('catalog-random-seed', random.random())
            if page == 1:
                seed = random.random()
            request.session['catalog-random-seed'] = seed
            request.session.save()
                
            random.seed(seed)

            if f == 'coming-soon':
#                date_x = datetime.now() + timedelta(30)
#                objects = objects.filter(Q(release_date__gt=datetime.now()) & Q(release_date__lte=date_x))
                objects = objects.filter(release_date__gt=datetime.now())

            if category or not request.user.is_authenticated():
                objects = list(objects)
            else:
                own_consoles = request.user.get_profile().get_owned_systems().order_by('-release_date', 'id')
                o1 = list(objects.filter(category__in=own_consoles))
                o2 = list(objects.exclude(category__in=own_consoles))
#                random.shuffle(o1)
#                random.shuffle(o2)
                objects = o1 + o2 

    paginator = Paginator(objects, settings.CATALOG_ITEMS_AMOUNT, 5)
    try:
        current_page = paginator.page(page)
    except Exception, e:
        debug(e)
        raise Http404()

    if request.is_ajax():
        items = []
        for o in current_page.object_list:
            items.append(get_item_json_synopsis(o))
        return JsonResponse({
            'status': 'OK',
            'items': items,
            'has_previous_page': current_page.has_previous(),
            'previous_page_number': current_page.previous_page_number(),
            'has_next_page': current_page.has_next(),
            'next_page_number' : current_page.next_page_number(),
            'page_number': page,
            'page_range': calc_paginator_ranges(paginator, page),
            'num_pages': paginator.num_pages,
        })
    else:
        return {
            'category': category,
            'filters': CATALOG_FILTERS,
            'filter': filter,
            'auto_filter': auto_filter,
            'genres': genres,
            'genre': genre,
            'page': current_page,
            'page_range': calc_paginator_ranges(paginator, page),
            'featured_games': featured_games,
        }

