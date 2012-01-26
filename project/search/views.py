from logging import debug

from django.shortcuts import redirect, render_to_response
from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django_snippets.views.json_response import JsonResponse
from django_snippets.views import simple_view
from django_snippets.utils.pagination import calc_paginator_ranges

from project.catalog.models import Item, Tag, Publisher
from django.utils.http import urlquote
from django.template.context import RequestContext
from project.catalog.models.categories import Category
from django.db.models.query_utils import Q
from django.template import defaultfilters


def get_item_json_synopsis(o):
    n = o.short_name
    if len(n) > 18:
        n = n[:18].strip() + '...'
    data = {
        'id': o.id,
        'short_name': n,
        'name': unicode(o),
        'url': o.get_absolute_url(),
        'actions': {},
        'cover': o.get_catalog_grid_cover(),
        'thumb_image': o.get_thumb_image(),
    }
    return data

def get_referer_path(request):
    from urlparse import urlsplit, urlunsplit
    from django.core.urlresolvers import resolve

    referer = request.META.get('HTTP_REFERER', '')
    o = urlsplit(referer)
    referer = urlunsplit((None, None, o.path, o.query, o.fragment))
    try:
        resolve(referer)
        return referer
    except:
        return None

@simple_view('search/results.html')
def search(request):
    if 'p' in request.REQUEST:
        try:
            page = int(request.REQUEST['p'])
        except:
            return redirect(request.META['PATH_INFO'])
    else:
        page = 1

    order_by = request.REQUEST.get('order_by') or request.session.get('SEARCH_ORDER_BY') or 0
    try:
        order_by = int(order_by)
        if order_by < 0 or order_by > 7:
            order_by = 0
    except:
        order_by = 0
    request.session['SEARCH_ORDER_BY'] = order_by
    
    title = ''
    category = None
    
    base_url = {}
    qs = Item.objects.filter(active=True)
    if qs: 
        c = request.REQUEST.get('platform', '')
        if c:
            try:
                category = Category.objects.get(name__iexact=c)
                qs = qs.filter(category=category)
                base_url['platform'] = c
            except Exception, e:
                qs = None
    tag = None
    if qs:
        tag = request.REQUEST.get('tag', '')
        if tag:
            try:
                title = tag
                qs = qs.filter(tags=Tag.objects.get(name__iexact=tag))
                base_url['tag'] = tag
            except:
                qs = None
    if qs:
        publisher = request.REQUEST.get('publisher', '')
        if publisher:
            try:
                title = publisher
                qs = qs.filter(publisher=Publisher.objects.get(name__iexact=publisher))
                base_url['publisher'] = publisher
            except:
                qs = None

    if qs:
        if order_by == 1: #Price: Low to High
            qs = qs.filter(rent_status__gt=0, retail_price_new__gt='0.0').order_by('retail_price_new')
        elif order_by == 2: #Price: High to Low
            qs = qs.filter(rent_status__gt=0, retail_price_new__gt='0.0').order_by('-retail_price_new')
        elif order_by == 3: #Value: Low to High
            qs = qs.filter(trade_flag=True, trade_price__gt='0.0').order_by('trade_price')
        elif order_by == 4: #Value: High to Low
            qs = qs.filter(trade_flag=True, trade_price__gt='0.0').order_by('-trade_price')
        elif order_by == 5: #Rent Availability
            qs = qs.filter(rent_status__lt=6).order_by('-rent_status')
        elif order_by == 6: #Release Date
            qs = qs.exclude(release_date=None).order_by('-release_date')
        elif order_by == 7: ## of Players
            qs = qs.order_by('-number_of_players')
    
    q = request.GET.get('q')
    if q:
        title = q
        base_url['q'] = q
        qs = Item.search_by_keyword(q, qs=qs)
        
    if title and category:
        title += ' (' + category.name + ')'
        
    title = title or 'All Games'

    base_url = '&'.join(['%s=%s' % (k, urlquote(v)) for k, v in base_url.items()])    

    paginator = Paginator(qs, settings.SEARCH_RESULTS_PER_PAGE, 2)
    try:
        current_page = paginator.page(page)
    except Exception, e:
        debug(e)
        raise Http404()

    page_range = calc_paginator_ranges(paginator, page)
            
    tags = {}
    for i in current_page.object_list:
        for t in i.tags.all():
            if t.name == tag:
                continue
            if t in tags:
                tags[t] += 1
            else:
                tags[t] = 1
    tags = tags.items()
    tags.sort(lambda a, b: cmp(b[1], a[1]))
    related_searches = []
    for t in tags[:3]:
        related_searches.append({
            'title': t[0].name,
            'url': t[0].get_absolute_url(),
        })

    referer = get_referer_path(request) or ''
    if referer.find('/Search/') >= 0 and 'search_referer' in request.session:
        search_referer = request.session['search_referer']
    else:
        search_referer = referer
        if referer:
            request.session['search_referer'] = referer

    if search_referer.find('/What-is-My-Game-Worth/') >= 0:
        source = 'What-is-My-Game-Worth'
    else:
        source = 'Video Games'
        search_referer = '/Search/'

    context = {
        'source': source,
        'search_referer': search_referer,
        'title': title,
        'base_url': base_url,
        'page': current_page,
        'page_range': page_range,
        'paginator': paginator,
        'order_by': order_by,
        'related_searches': related_searches,
    }
    if request.is_ajax():
        return render_to_response('search/results-grid.html', context, RequestContext(request))
    return context


def by_upc(request):
    qs = Item.objects.filter(active=True)
    q = request.REQUEST.get('q')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(upc__icontains=q))
    r = []
    for i in qs.values('upc', 'name', 'category__name', 'id'):
        r.append(u'<b>{upc}</b> {name} ({category__name})|{id}|{upc}'.format(**i))
    return HttpResponse('\n'.join(r))


def by_upc2(request):
    qs = Item.objects.all()
    q = request.REQUEST.get('q')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(upc__icontains=q))
    r = []
    for i in qs.values('upc', 'name', 'category__name', 'id'):
        r.append(u'<b>{upc}</b> {name} ({category__name})|{id}|{upc}'.format(**i))
    return HttpResponse('\n'.join(r))


def quick(request):
    if not request.is_ajax():
        return redirect('search:search')

    q = request.REQUEST.get('q')
    qs = Item.search_by_keyword(q)
        
    try:        
        res = []
        for i in qs[:7]:
            res.append({
                'url': i.get_absolute_url(),
                'title': i.get_cropped_name() + ' ' + unicode(i.category),
                'upc': i.upc,
                'release_date': defaultfilters.date(i.release_date) if i.release_date else None,
                'icon': i.get_nano_thumb(),
            })
    except Exception, e:
        debug(e)
    return JsonResponse({'status': 'ok', 'items': res})
