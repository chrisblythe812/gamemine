import datetime
import logging

from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import defaultfilters
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from django_snippets.views import simple_view, JsonResponse

from project.catalog.models import Item, Review, ItemVote
from project.reviews.utils import render_review_form
from project.rent import get_minimal_rent_charge
from project.catalog.models.items import ItemViewsStat

logger = logging.getLogger(__name__)


@simple_view('catalog/item.html')
def item(request, item_slug, id):
    try:
        item = get_object_or_404(Item, id=id, slug=item_slug)
        ItemViewsStat.inc(item)
    except Exception, e:
        logger.debug(e)
        raise
    return {
        'item': item,
        'category': item.category,
        'item_rent_status': item.get_rent_status(request.user),
    }


def get_item_hint_details(item, request):
    buy_price = item.get_min_price()
    return {
        'picture': '',
        'ratio': '{0:.1f}'.format(item.ratio) if item.ratio else 'N/A',
        'percents': int(20.0 * item.ratio),
        'publisher': unicode(item.publisher),
        'release_date': defaultfilters.date(item.release_date),
        'rating': unicode(item.rating),
        'genres': ', '.join(item.genre_names()),
        'number_of_players': item.number_of_players,
        'cover': item.get_cover(),
        'inventory': {
            'buy': '$%s' % buy_price if buy_price else '--',
            'rent': item.get_rent_status(request.user, short_na=True),
            'trade': '$%s' % item.trade_price if item.trade_flag and item.trade_price>0 else '--',
        },
    }


def get_review_details(r, request):
    res = {
        'id': r.id,
        'title': r.title,
        'comment': defaultfilters.linebreaksbr(r.comment),
        'ratio': int(r.rating) * 20,
        'user': {
            'icon': r.user.get_profile().get_icon_url(),
        },
        'own_review': r.user == request.user,
        'posted_by': 'Posted %s ago by %s' % (defaultfilters.timesince(r.timestamp), r.user.username),
    }
    return res


def get_item_ratio(item, request):
    my_rate = 0
    if request.user.is_authenticated():
        qs = ItemVote.objects.filter(item=item, user=request.user, review=None)
        if qs.count():
            my_rate = qs[0].ratio

    res = {
        'ratio': {
            'percents': item.ratio_percents(),
            'ratio': defaultfilters.floatformat(item.ratio, 1) if item.ratio else 'N/A',
            'rating': item.ratio5,
        },
        'votes': item.votes,
        'my_rate': my_rate,
    }
    return res


def get_item_details(item, request):
    the_reviews = Review.get_for_object(item)
    reviews_count = settings.DEFAULT_REVIEWS_COUNT if request.user.is_authenticated() else 1

    data = {
        'id': item.id,
        'title': unicode(item),
        'url': item.get_absolute_url(),
        'description': defaultfilters.linebreaksbr(item.description),
        'cover': item.get_cover(),
        'release_date': defaultfilters.date(item.release_date) if item.release_date else None,
        'publisher': {
            'name': item.publisher.name if item.publisher else None,
            'url': item.publisher.get_absolute_url() if item.publisher else None,
        },
        'esrb': item.rating.title if item.rating else None,
        'number_of_players': item.number_of_players,
        'number_of_online_players': item.number_of_online_players,
        'genres': [{'name': unicode(x), 'url': '%s?genre=%d' % (reverse('catalog:category', args=[item.category.slug]), x.id), } for x in item.genres.all()],
        'tags': [{'name': unicode(x), 'url': x.get_absolute_url(), } for x in item.tags.all()],
        'platform': {
            'name': item.category.description,
            'url': item.category.get_absolute_url(),
        },
        'also_on': [{'name': x.category.description, 'url': x.get_absolute_url()} for x in item.also_on()],
        'reviews': {
            'count': the_reviews.count(),
            'items': [get_review_details(r, request) for r in the_reviews[:reviews_count]],
        },
        'screenshots': item.get_screenshots(),
        'media_details': reverse('catalog:item_action', args=[item.slug, item.id, 'media-details']),
        'authenticated': request.user.is_authenticated(),
        'actions': {},
    }
    data.update(get_item_ratio(item, request))
    if request.user.is_authenticated():
        data['reviews']['form'] = render_review_form(request, item)
#    if item.available_for_selling():
    data['actions']['buy'] = {
        'url': reverse('cart:add', args=[item.id]),
        'price': item.get_retail_prices_display(),
    }
#    if item.rent_flag:
    if request.user.is_authenticated():
        msg = '<em>AVAILABILITY</em></br> %s' % item.get_rent_status(request.user)
    else:
        msg = 'Only <a href="%s" class="link-dialog">$%s</a> a month' % (
            reverse('new_rent:sign_up'), get_minimal_rent_charge())
    data['actions']['rent'] = {
        'url': reverse('rent:add', args=[item.id]),
        'price': msg,
    }
#    if item.rent_flag:
    data['actions']['trade'] = {
        'url': reverse('trade:add', args=[item.id]),
        'price': item.get_trade_prices_display(),
    }
    return data


def get_muze_description(item, request):
    return {
        'description': {
            'expanded': item.get_muze_description(),
        },
    }


def get_more_reviews(item, request):
    try:
        id = int(request.REQUEST.get('id'))
        if not id:
            raise Exception()
    except:
        return HttpResponseBadRequest()
    if not request.user.is_authenticated():
        return {
            'reviews': [],
            'has_more_reviews': False,
        }
    reviews = Review.get_for_object(item).filter(id__lt=id)
    return {
        'reviews': [get_review_details(r, request) for r in reviews[:settings.DEFAULT_REVIEWS_COUNT]],
        'has_more_reviews': reviews.count() > settings.DEFAULT_REVIEWS_COUNT,
    }


def get_all_reviews(item, request):
    if not request.user.is_authenticated():
        return {
            'reviews': [],
            'has_more_reviews': False,
        }
    reviews = Review.get_for_object(item)
    return {
        'reviews': [get_review_details(r, request) for r in reviews[:settings.DEFAULT_REVIEWS_COUNT]],
        'has_more_reviews': reviews.count() > settings.DEFAULT_REVIEWS_COUNT,
    }


def get_helpful_reviews(item, request):
    if not request.user.is_authenticated():
        return {
            'reviews': [],
            'has_more_reviews': False,
        }
    reviews = Review.get_helpful(item)
    return {
        'reviews': [get_review_details(r, request) for r in reviews[:settings.DEFAULT_REVIEWS_COUNT]],
        'has_more_reviews': reviews.count() > settings.DEFAULT_REVIEWS_COUNT,
    }


def get_media_details(item, request):
    ctx = {
        'item': item,
        'screenshots': item.get_screenshots(),
        'videos': item.get_videos2(),
    }
    return render_to_response('catalog/partials/media_details.html', ctx, RequestContext(request))


def item_action(request, item_slug, id, action):
    item = get_object_or_404(Item, id=id, slug=item_slug)
    if not settings.DEBUG and not request.is_ajax():
        return redirect(item.get_absolute_url())
    response = {
        'hint-details': get_item_hint_details,
        'details': get_item_details,
        'muze-description': get_muze_description,
        'get-more-reviews': get_more_reviews,
        'get-all-reviews': get_all_reviews,
        'get-helpful-reviews': get_helpful_reviews,
        'media-details': get_media_details,
    }[action](item, request=request)
    if isinstance(response, HttpResponse):
        return response
    return JsonResponse(response)


@login_required
def rate(request, id, rating):
    item = get_object_or_404(Item, id=id)
    if not request.is_ajax():
        return redirect(item.get_absolute_url())

    qs = ItemVote.objects.filter(item=item, user=request.user, review=None)
    if qs.count():
        vote = qs[0]
        vote.ratio=int(rating)
    else:
        vote = ItemVote(item=item, user=request.user, ratio=int(rating))

    vote.ip_address = request.META.get("REMOTE_ADDR", None)
    vote.timestamp = datetime.datetime.now()
    vote.save()
    return JsonResponse(get_item_details(vote.item, request))


def mark_useful(request, id, vote):
    if not request.user.is_authenticated():
        return JsonResponse({'status': 'fail'})
    review = get_object_or_404(Review, id=id)
    if not request.is_ajax():
        return redirect(review.content_object.get_absolute_url())
    vote = 1 if vote == 'yes' else -1
    review.vote_for_review(request.user, vote)
    return JsonResponse({'status': 'ok'})


@login_required
def delete_rate(request, id):
    vote = get_object_or_404(ItemVote, id=id, user=request.user)
    if not request.is_ajax():
        return redirect(vote.item.get_absolute_url())

    vote.delete();
    ratings = ItemVote.objects.filter(review=None, user=request.user).order_by('-timestamp')
    res = {
        'status': 'ok',
        'table': render_to_string('members/profile/game_ratings.table.html',
                                  {'ratings': ratings, },
                                  RequestContext(request)),
    }
    return JsonResponse(res)


@login_required
def delete_review(request, id):
    vote = get_object_or_404(ItemVote, id=id, user=request.user)
    if not request.is_ajax():
        return redirect(vote.item.get_absolute_url())

    vote.delete();
    ratings = ItemVote.objects.exclude(review=None).filter(user=request.user).order_by('-timestamp')
    res = {
        'status': 'ok',
        'table': render_to_string('members/profile/game_reviews.table.html',
                                  {'reviews': ratings, },
                                  RequestContext(request)),
    }
    return JsonResponse(res)


@login_required
@simple_view('members/profile/edit_review.html')
def edit_review(request, id):
    review = get_object_or_404(ItemVote, id=id, user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        try:
            rating = int(request.POST.get('rating', 5))
        except:
            rating = 5
        if comment:
            review.review.title = title
            review.review.comment = comment
            review.review.rating = rating
            review.review.save()
            review.ratio = rating
            review.save()
            return redirect('members:profile_game_reviews')

    form_data = {
        'title': review.review.title,
        'comment': review.review.comment,
        'rating': review.ratio,
    }
    return {
        'review': review,
        'form_data': form_data,
    }
