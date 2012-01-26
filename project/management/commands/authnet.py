# * coding=utf-8 *

from django.core.management.base import LabelCommand
from django.conf import settings

from authorizenet import AIM


class Command(LabelCommand):
    args = '[test]'
    help = 'Working with authorize.net'
    label = 'command'

    def handle_label(self, label, **options):
        if label == 'test':
            self.do_test()

    def do_test(self):
        test_card = settings.AUTH_NET_CONF.pop('test_card')
        aim = AIM(**settings.AUTH_NET_CONF)
        aim.test(**test_card)
