import re
import itertools
import MySQLdb

from django.core.management.base import LabelCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User

from project.members.models import Profile, BillingCard


class Command(LabelCommand):
    args = '[link_to_dc]'
    help = 'Working with members'
    label = 'command'

    def handle_label(self, label, **options):
        getattr(self, 'do_' + label)()
        
    def do_link_to_dc(self):
        if not settings.MELISSA:
            raise CommandError('You must activate melissa usage before run this command.')
        count = Profile.objects.count()
        for i, p in itertools.izip(itertools.count(1), Profile.objects.all()):
            if i % 100 == 0:
                print 'Processed %s of %s...' % (i, count)
            zip = (p.shipping_zip or '').split('-')[0]
            if not re.match(r'^\d{5}$', zip):
                continue
            if not p.dropship:
                p.link_to_dropship()

        from project.inventory.models import Dropship
        print "Members in dropships:"
        for dc in Dropship.objects.all():
            print "\t%s: %d" % (dc.name, dc.members.all().count())
    
    def do_update_cards(self):
        for card in BillingCard.objects.all():
            card.save()

    def do_fix_names(self):
        for u in User.objects.raw('SELECT id, first_name, last_name from auth_user where first_name = lower(first_name) or last_name = lower(last_name) order by id'):
            name = settings.MELISSA.inaccurate_name(full_name=u.get_full_name())
            u.first_name = name['first_name']
            u.last_name = name['last_name']
            u.save()
            print u.id, '\t', u.get_full_name()

    def _get_cursor(self):
        if not hasattr(self, 'mconn'):
            self.mconn = MySQLdb.connect(host='78.31.177.17', db="gamemine", user='gamemine', passwd='1')
        return self.mconn.cursor()

    def do_fix_phones(self):
        cursor = self._get_cursor()
        cursor.execute("SELECT count(id) FROM members m where phone is not null and phone <> ''", [])
        amount = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, phone FROM members m where phone is not null and phone <> ''", [])
        for i, (id, phone) in enumerate(cursor.fetchall()):
            if i % 100 == 0 and i:
                print '%d of %d' % (i, amount)
            try:
                p = Profile.objects.get(user__id=id)
            except Profile.DoesNotExist:
                continue

            p.phone = settings.MELISSA.inaccurate_phone(phone, zip=p.shipping_zip)
            p.save()

    def do_calc_checksums(self):
        for p in Profile.objects.all():
            p.calc_shipping_checksum()
