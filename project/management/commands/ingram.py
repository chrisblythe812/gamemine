from decimal import Decimal
from datetime import datetime
from zipfile import ZipFile
from optparse import make_option
import os
import logging
from ftplib import FTP

from django.core.management.base import BaseCommand
from django.conf import settings

from project.catalog.models.items import Item
from project.inventory.models import DistributorItem
import sys
import tempfile


info = logging.getLogger('crontab').info
error = logging.getLogger('crontab').error
debug = logging.getLogger('crontab').debug
warn = logging.getLogger('crontab').warn


def parse_line(r, *args):
    r = r.rstrip().split(';')
    return r if len(r) > 1 else None

class Command(BaseCommand):
    option_list = (
        make_option('-v', '--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option('--settings',
            help='The Python path to a settings module, e.g. "myproject.settings.main". If this isn\'t provided, the DJANGO_SETTINGS_MODULE environment variable will be used.'),
        make_option('--pythonpath',
            help='A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".'),
        make_option('--traceback', action='store_true',
            help='Print traceback on exception'),
        make_option('--games'),
        make_option('--qtygames'),
    )

    def handle(self, *args, **options):
        files = []
        try:
            info('Updating games from INGRAM...')

            games = options.get('games')

            if not games:
                ftp = settings.INGRAM['ftp']
                ftp_host = ftp['host']
                ftp_username = ftp['username']
                ftp_password = ftp['password']
                print 'Connecting to ftp://%s@%s' % (ftp_username, ftp_host)
                ftp = FTP(ftp_host)
                ftp.login(ftp_username, ftp_password)

                def get_file(filename):
                    print 'Downloading %s...' % filename
                    fd, fname = tempfile.mkstemp()
                    files.append(fd)
                    ftp.retrbinary('RETR %s' % filename, lambda b: os.write(fd, b))
                    return fname

                games = get_file('/pub/games.zip')
                qtygames = get_file('/pub/qtygames.zip')
            else:
                games = os.path.expanduser(games)
                qtygames = os.path.expanduser(options['qtygames'])

            print 'Processing games...'

            inventory = {}

            z = ZipFile(qtygames, 'r')
            for rr in z.open('GAMESQ.DAT').readlines():
                r = parse_line(rr)
                if not r: continue
                item_number = r[0].strip()
                upc = r[2].strip()
                quantity = int(r[4].rstrip('0') or '0')
                in_stock = r[3].strip() in ['', 'S']
                inventory[item_number] = {'upc': upc, 'quantity': quantity, 'in_stock': in_stock}
    #            print '\t'.join(map(str, (item_number, upc, quantity)))

            unknown_items = []
            items = []

            DistributorItem.objects.filter(distributor__id=5).delete()

            platform_map = {
                'X360': 'Xbox-360-Games',
                'WII': 'Nintendo-Wii-Games',
                'XBOX': 'Xbox-Games',
                'NINTENDO': 'GameCube-Games',
                'PS2': 'PlayStation-2-Games',
                'PS3': 'PlayStation-3-Games',
                'NDS': 'Nintendo-DS-Games',
                'PSP': 'Sony-PSP-Games',
                '3DS':'3DS-Games',
            }

            z = ZipFile(games, 'r')
            for rr in z.open('GAMESC.DAT').readlines():
                r = parse_line(rr)
                if not r: continue

                item_number = r[0].strip()
                upc = r[6].strip()
                retail_price = Decimal(r[4])
                prebook_date = datetime.strptime(r[8], '%Y/%m/%d')
                release_date = datetime.strptime(r[9], '%Y/%m/%d')
                weight = Decimal(r[28]) * 16
                class_code = int(r[29][2:])
                try:
                    item = Item.objects.get(upc=upc)
                    item.base_retail_price_new = retail_price
                    item.recalc_prices(prices=['retail_price_new'], save=False)
                    item.prebook_date = prebook_date
                    item.game_weight = weight
#                    if class_code not in [200, 211, 212, 213, 214, 215, 216, 217, 218] or item.name.upper().find('BUNDLE') != -1:
#                        item.trade_flag = False
#                        item.rent_flag = False
#                    elif class_code in [200, 211, 212, 213, 214, 215, 216, 217, 218]:
#                        item.trade_flag = True
#                        item.rent_flag = True
#                        item.active = True
                    if release_date > datetime.today():
                        item.release_date = release_date
                    item.save()

                    if inventory[item_number]['quantity']:#inventory[item_number]['in_stock']:
                        DistributorItem(distributor_id=5,
                                        item=item,
                                        is_new=True,
                                        retail_price=retail_price,
                                        quantity=inventory[item_number]['quantity']).save()

                    items.append(item)
                except Item.DoesNotExist:
                    if class_code in [200, 211, 212, 213, 214, 215, 216, 217, 218] and r[2].split()[0] in platform_map and inventory[item_number]['quantity'] > 0:
                        unknown_items.append(r)
#                        print '\t'.join(r)

            info('INGRAM done. Updated %d items' % len(items))
        except Exception, _e:
            error('Error occurs when trying to update games from INGRAM', exc_info=sys.exc_info())
        map(os.close, files)

