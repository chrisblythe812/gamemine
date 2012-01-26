from django import template

register = template.Library()


@register.filter(name='percents')
def percents(value, arg):
    value = float(value)
    arg = float(arg)
    return int(value / arg * 100) if arg else 0
