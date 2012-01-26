from logging import error, debug #@UnusedImport
import xlrd #@UnresolvedImport
import itertools
from datetime import datetime
import yaml
import tempfile

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from project.catalog.models import Category, Publisher, Genre, Tag, Type, Game, Rating
from project.catalog.models.items import Item #@UnusedImport

def memoize(function):
    # return function
    cache = {}
    def decorated_function(*args):
        if args in cache:
            return cache[args]
        else:
            val = function(*args)
            cache[args] = val
            return val
    return decorated_function

class ReadException(Exception):
    def __init__(self, data):
        self.data = data

class Command(BaseCommand):
    args = '<XLS filename>'
    help = 'Import data from Master Product List'

    def handle(self, xls_filename=None, *args, **options):
        if not xls_filename:
            raise CommandError('Please specify a filename.')

        def log(s):
            debug(s)

        data = self.read_mpl(xls_filename, log)
        self.deserialize(data, log)


    def read_mpl(self, xls_filename, log=None):
        log = log or (lambda x: None)

        log('Opening %s...' % xls_filename)
        wb = xlrd.open_workbook(xls_filename)
        log('Opening first sheet...')
        sh = wb.sheet_by_index(0)
        log('Loading %d row(s)...' % (sh.nrows - 1))
        titles = map(lambda x: x.encode('utf-8'), sh.row_values(0))
        ready_to_deserialize = []
        for r in range(1, sh.nrows):
            if r > 1 and (r - 1) % 100 == 0:
                log('Prepared %d rows...' % (r - 1))
            row = map(self._translate_value, sh.row_values(r))
            data = dict(itertools.izip(titles, row))
            try:
                if Item.objects.filter(upc=data['UPC']).count():
                    item = Item.objects.get(upc=data['UPC'])
                    item.trade_flag = int(data['TRADE_FLAG'] or '0') != 0
                    item.rent_flag = int(data['RENT_FLAG'] or '0') != 0
                    item.active = int(data['DISPLAY_ON_SITE_FLAG'] or '0') != 0
                    item.name = data['PRODUCT_NAME_LONG'],
                    item.short_name = data['PRODUCT_NAME_SHORT'],
                    item.slug = data['SLUG'],
                    item.description = data['PRODUCT_DESCRIPTION'],
                    item.save()
                    continue

                pk = data['PID']
#                base_retail_price = '%0.2f' % data['MSRP_GM'] if isinstance(data['MSRP_GM'], float) else None
                upc = '%s' % data['UPC']
                if upc.find('.') != -1:
                    upc = upc.split('.')[0]
                upc = '0' * (12 - len(upc)) + upc
                number_of_players = data.get('NUMBER_OF_PLAYERS', '').replace('-', '') or None
                tags = data.get("TAGS") or data.get("GENRE_TAGS")

                ready_to_deserialize.append({
                    'pk': pk,
                    'model': 'catalog.item',
                    'fields': {
                        'upc': upc,
                        "ingram_code": data.get("INGRAM_CODE"),
                        'name': data['PRODUCT_NAME_LONG'],
                        'short_name': data['PRODUCT_NAME_SHORT'],
                        'slug': data['SLUG'],
                        'description': data['PRODUCT_DESCRIPTION'],
                        'category': self._get_category(data['PLATFORM_SHORT_NAME']).id,
                        'number_of_players': number_of_players,
                        'number_of_online_players': number_of_players,
                        'release_date': datetime(*xlrd.xldate_as_tuple(data['RELEASE_DATE'], 0)) if data['RELEASE_DATE'] not in ['TBD', ''] else None,
                        'game': self._get_game(data['PRODUCT_NAME_SHORT']).id,
                        'rating': self._get_rating(data['ESRB_NAME_SHORT']),
                        'publisher': self._get_publisher(data['PUBLISHER_NAME']),
                        'trade_flag': int(data['TRADE_FLAG'] or '0') != 0,
                        'rent_flag': int(data['RENT_FLAG'] or '0') != 0,
                        'active': int(data['DISPLAY_ON_SITE_FLAG'] or '0') != 0,
                        'type': 1,
                        'genres': map(lambda x: x.id, self._get_genres(data['GENRE_NAME'])),
                        'tags': map(lambda x: x.id, self._get_tags(tags)),
                    }
                })
            except Exception, e:
                error(e)
                raise ReadException(data)

        return ready_to_deserialize

    def deserialize(self, data, log):
        log = log or (lambda x: None)

        log('Processing %d objects...' % len(data))

        with tempfile.NamedTemporaryFile(suffix='.yaml') as f:
            log('Dumping fixture to temporary file %s...' % f.name)
            yaml.dump(data, stream=f, default_flow_style=False, line_break=True)
            call_command('loaddata', f.name)

    '''
    @transaction.commit_on_success
    def mass_insert(self, data, log):
        keys = data[0]['fields']
        del keys['tags']
        del keys['genres']
        keys = keys.keys()

        keys = [key if key != 'category' else 'category_id' for key in keys]
        keys = [key if key != 'rating' else 'rating_id' for key in keys]
        keys = [key if key != 'publisher' else 'publisher_id' for key in keys]
        keys = [key if key != 'game' else 'game_id' for key in keys]
        keys = [key if key != 'type' else 'type_id' for key in keys]
        keys.append('profit')
        keys.append('wholesale_price_used')
        keys.append('quantity_used')
        query = 'INSERT INTO catalog_item (id,' + ','.join(keys) + ')VALUES(%s' + (',%s' * len(keys)) + ');'

        from django.db import connection, transaction
        cursor = connection.cursor()
        for item in data:
            if Item.objects.filter(id=item['pk']).count():
                continue

            f = item['fields']
            try:
                del f['tags']
                del f['genres']
            except:
                pass

            row = f.values()
            row.insert(0, item['pk'])
            row.append('0')
            row.append('0')
            row.append('0')
            cursor.execute(query, row)
        transaction.set_dirty()
    '''

    def _translate_value(self, v):
        if isinstance(v, unicode):
            return v.encode('utf-8')
        return v

    @memoize
    def _get_category(self, platform):
        platform = {
            'GCUBE': 'GameCube-Games',
            'NDS': 'Nintendo-DS-Games',
            'DS': 'Nintendo-DS-Games',
            'PS2': 'PlayStation-2-Games',
            'PS3': 'PlayStation-3-Games',
            'PSP': 'Sony-PSP-Games',
            'WII': 'Nintendo-Wii-Games',
            'X360': 'Xbox-360-Games',
            'XBOX': 'Xbox-Games',
            '3DS':'Nintendo-3DS-Games',
        }[platform.upper()]
        return Category.objects.get(slug=platform)

    @memoize
    def _get_default_type(self):
        return Type.objects.get(pk=1)

    @memoize
    def _get_rating(self, rating):
        try:
            return Rating.objects.get(esrb_symbol=rating).id if rating else None
        except:
            return None

    @memoize
    def _get_publisher(self, name):
        name = name.strip()
        try:
            return Publisher.objects.get(name__iexact=name, type=self._get_default_type()).id if name else None
        except:
            o = Publisher(name=name, type=self._get_default_type())
            o.save()
            return o.id

    @memoize
    def _get_genre(self, name):
        name = name.strip()
        try:
            return Genre.objects.get(name__iexact=name, type=self._get_default_type())
        except:
            o = Genre(name=name, type=self._get_default_type())
            o.save()
            return o

    def _get_genres(self, names):
        for n in names.split(','):
            yield self._get_genre(n)

    @memoize
    def _get_tag(self, name):
        name = name.strip()
        try:
            return Tag.objects.get(name__iexact=name)
        except:
            o = Tag(name=name)
            o.save()
            return o

    def _get_tags(self, names):
        for n in names.split(','):
            yield self._get_tag(n)

    @memoize
    def _get_game(self, name):
        name = name.strip()
        try:
            return Game.objects.get(name__iexact=name)
        except:
            o = Game(name=name)
            o.save()
            return o

