import re

from django import template

from project.banners.models import ListPageBanner

register = template.Library()


class RandomBannerNode(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        context[self.var_name] = ListPageBanner.objects.get_random()
        return ''


@register.tag
def random_banner(parser, token):
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r'as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    var_name = m.groups()[0]
    return RandomBannerNode(var_name)
