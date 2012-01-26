from authorizenet import AIM

from django.conf import settings


def aim_logger(*args, **kwargs):
    from project.staff.models import aim_logger as the_logger
    the_logger(*args, **kwargs)


def create_aim():
    return AIM(logger=aim_logger, **settings.AUTH_NET_CONF)


def get_melissa():
    if settings.MELISSA_CONFIG['use_melissa']:
        from melissadata import Melissa
        return Melissa(settings.MELISSA_CONFIG)
    else:
        return None
