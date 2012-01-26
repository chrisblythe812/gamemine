from logging import debug #@UnusedImport

from django import template
from django.utils.safestring import mark_safe

from project.catalog.models.item_votes import ItemVote

register = template.Library()

@register.filter
def star_rating(item, user=None):
    active = not user or user.is_authenticated()
    if active: 
        return mark_safe('''<ul class="rating stars%(ratio)d">
    	    <li class="star1"><a href="/Rate/%(id)d/1/" title="1 Star">1</a></li>
    	    <li class="star2"><a href="/Rate/%(id)d/2/" title="2 Stars">2</a></li>
    	    <li class="star3"><a href="/Rate/%(id)d/3/" title="3 Stars">3</a></li>
    	    <li class="star4"><a href="/Rate/%(id)d/4/" title="4 Stars">4</a></li>
    	    <li class="star5"><a href="/Rate/%(id)d/5/" title="5 Stars">5</a></li>
        </ul>''' % {'ratio': int(item.ratio), 'id': item.id})
    else:
        return mark_safe('''<ul class="rating stars%(ratio)d">
            <li class="star1">1</li>
            <li class="star2">2</li>
            <li class="star3">3</li>
            <li class="star4">4</li>
            <li class="star5">5</li>
        </ul>''' % {'ratio': int(item.ratio), 'id': item.id})

@register.filter
def genre_rating(genre):
    return mark_safe('''<ul class="rating stars%(ratio)d">
        <li class="star1"><a href="/Genre/%(id)d/Rate/1/" class="grid-action" title="1 Star">1</a></li>
        <li class="star2"><a href="/Genre/%(id)d/Rate/2/" class="grid-action" title="2 Stars">2</a></li>
        <li class="star3"><a href="/Genre/%(id)d/Rate/3/" class="grid-action" title="3 Stars">3</a></li>
        <li class="star4"><a href="/Genre/%(id)d/Rate/4/" class="grid-action" title="4 Stars">4</a></li>
        <li class="star5"><a href="/Genre/%(id)d/Rate/5/" class="grid-action" title="5 Stars">5</a></li>
    </ul>''' % {'ratio': int(genre[1]), 'id': genre[0].id})


@register.filter
def rate_game(item, user):
    v = 0
    if user.is_authenticated():
        qs = ItemVote.objects.filter(user=user, item=item, review=None)
        if qs.count():
            v = qs[0].ratio
        
    return mark_safe('''<ul class="my large rating stars%(value)s">
        <li class="star1"><a href="/Rate/%(id)d/1/" title="1 Star">1</a></li>
        <li class="star2"><a href="/Rate/%(id)d/2/" title="2 Stars">2</a></li>
        <li class="star3"><a href="/Rate/%(id)d/3/" title="3 Stars">3</a></li>
        <li class="star4"><a href="/Rate/%(id)d/4/" title="4 Stars">4</a></li>
        <li class="star5"><a href="/Rate/%(id)d/5/" title="5 Stars">5</a></li>
    </ul>''' % {'ratio': int(item.ratio), 'id': item.id, 'value': v})

