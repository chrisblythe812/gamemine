from django import template

register = template.Library()


@register.inclusion_tag("catalog/sidebar-advertisement.html", takes_context=True)
def sidebar_advertisement(context):
    if context["eligible_for_free_trial"]:
        rent_img = "/RENT_Television_freetrial.jpg"
    else:
        rent_img = "/RENT_Television.jpg"
    return {
        "STATIC_URL": context["STATIC_URL"],
        "REV": context["REV"],
        "rent_img": rent_img,
    }
