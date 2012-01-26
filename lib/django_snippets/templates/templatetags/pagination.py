from django import template

register = template.Library()

@register.inclusion_tag('pagination.html',takes_context=True)
def pagination(context,adjacent_pages=5):
    page_list = range(
        max(1,context['page'] - adjacent_pages),
        min(context['pages'],context['page'] + adjacent_pages) + 1)
    lower_page = None
    higher_page = None

    if not 1 == context['page']:
        lower_page = context['page'] - 1

    if not 1 in page_list:
        page_list.insert(0,1)
        if not 2 in page_list:
            page_list.insert(1,'.')

    if not context['pages'] == context['page']:
        higher_page = context['page'] + 1

    if not context['pages'] in page_list:
        if not context['pages'] - 1 in page_list:
            page_list.append('.')

        page_list.append(context['pages'])

    get_params = u'?'
    for k in context['request'].GET:
        if k==u'page':
            continue
        if get_params!=u'?':
            get_params+=u'&'
        get_params+=u"%s=%s" % (k,context['request'].GET.get(k, u''))
    if get_params!=u'?':
        get_params+=u'&'

    return {
        'get_params': get_params,
        'lower_page': lower_page,
        'higher_page': higher_page,
        'page': context['page'],
        'pages': context['pages'],
        'page_item_count': context['count'],
        'page_list': page_list,
        'STATIC_URL': context['STATIC_URL'],
    }
