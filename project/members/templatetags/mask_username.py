from logging import debug

from django.template.defaultfilters import stringfilter, register


@register.filter
@stringfilter
def mask_username(value):
    debug(value.encode('utf8').find('@'))
    if value.encode('utf8').find('@') == -1:
        return value
    return value.split('@')[0] + '@...'
