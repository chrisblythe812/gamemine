from django.core.management.base import LabelCommand
from django.conf import settings
import itertools

from melissadata import Melissa

from project.members.models import Profile
from melissadata.errors import MelissaAddressError
from django.contrib.auth.models import User


class Command(LabelCommand):
    args = '[test, udpate_addresses, fix_names]'
    help = 'Working with melissadata'
    label = 'command'

    def handle_label(self, label, **options):
        if label == 'test':
            self.do_test()
        elif label == 'udpate_addresses':
            self.do_udpate_addresses()
        elif label == 'fix_names':
            self.do_fix_names()

    def do_test(self):
        m = Melissa(settings.MELISSA_CONFIG)
        m.test()

    def do_udpate_addresses(self):
        count = Profile.objects.count()
        print 'Initializing melissa...'
        melissa = Melissa(settings.MELISSA_CONFIG)
        print 'Found %d profiles' % count
        for p, i in itertools.izip(Profile.objects.all().select_related(), itertools.count(1)):
            if i % 100 == 0:
                print 'Processed %d of %d profiles...' % (i, count)

            addr = p.get_billing_address_data()
            if not addr.get('address1'):
                continue          
            print addr.values()
            print '>', u', '.join(map(lambda x: x or '', addr.values()))
            try:
                addr = melissa.inaccurate_address(**addr)
                print ' ', addr['county']
            except MelissaAddressError, e:
                print '!', e, u', '.join(map(lambda x: x or '', addr.values()))
            except Exception, e:
                print '!', e, u', '.join(map(lambda x: x or '', addr.values()))
        print 'OK'

    def do_fix_names(self):
        print 'Fixing names...'
        for user in User.objects.all():
            name = {'full_name': user.get_full_name() }
            try:
                name = settings.MELISSA.inaccurate_name(**name)
                user.first_name = name['first_name']
                user.last_name = name['last_name']
                user.save()
            except Exception, e:
                print e

