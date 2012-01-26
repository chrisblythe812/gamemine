import operator
import os
import decimal
from datetime import datetime, timedelta

from logging import debug, error #@UnusedImport

from django.db import models, transaction
from django.conf import settings
from django.template import defaultfilters
from django.utils.safestring import mark_safe
from django_snippets.thirdparty.models import JSONField

from categories import Category
from types import Type
from ratings import Rating
from publishers import Publisher
from games import Game
from genres import Genre
from tags import Tag

from project.rent import is_item_at_home, list_games_at_home, is_item_on_list,\
    is_item_at_shipping_process
from project.discount.models import DiscountCalculator
from django.db.models.aggregates import Sum


def required_muze_cache(part, force=False):

    def get_screenshots(work_id):
        return settings.MUZE.get_screenshots(work_id)

    def get_videos(work_id):
        videos = settings.MUZE.get_videos(work_id)
        videos = filter(lambda x: x['file_name'].endswith('.flv'), videos)
        return videos

    def get_videos2(work_id):
        videos = settings.MUZE.get_videos2(work_id)
#        videos = filter(lambda x: x['file_name'].endswith('.flv'), videos)
        return videos

    def get_expanded_description(work_id):
        return settings.MUZE.get_expanded_description(work_id)

    def get_front_image(work_id):
        return settings.MUZE.get_front_image(work_id)

    def get_msrp(work_id):
        return settings.MUZE.get_msrp(work_id)

    calls_map = {'screenshots': get_screenshots,
                 'videos': get_videos,
                 'videos2': get_videos2,
                 'expanded_description': get_expanded_description,
                 'front_image': get_front_image,
                 'msrp': get_msrp,}

    def decorator(func):
        def real_decorator(item, *args, **kwargs):
            save = False
            if not force:
                cache = item.muze_cache if isinstance(item.muze_cache, dict) else {}
            else:
                cache = {}

            if not cache:
                save = True
                cache = {'work_id': settings.MUZE.get_work_id(item.upc)}
            work_id = cache['work_id']
            if part not in cache:
                save = True
                cache[part] = calls_map[part](work_id)
            if save:
                item.muze_cache = cache
                item.save()
            return func(item, *args, **kwargs)
        return real_decorator
    return decorator


class ItemManager(models.Manager):
    def category_by_platform(self, platform):
        try:
            platform = {
                'GCUBE': 'GameCube-Games',
                'NDS': 'Nintendo-DS-Games',
                'PS2': 'PlayStation-2-Games',
                'PS3': 'PlayStation-3-Games',
                'PSP': 'Sony-PSP-Games',
                'WII': 'Nintendo-Wii-Games',
                'X360': 'Xbox-360-Games',
                'XBOX': 'Xbox-Games',
            }[platform.upper().replace('360','X360')]
            return Category.objects.get(slug=platform)
        except:
            return None

    def get_default_type(self):
        return Type.objects.get(pk=1)

    def active(self):
        return Item.objects.filter(active=True, category__active=True)

    def top_rentals(self):
        return self.active().filter(rent_amount__gt=0).order_by('-rent_amount', 'id')

    def popular(self):
        return self.order_by('-ratio')

    def new_releases(self):
        date_x = datetime.now() - timedelta(60)
        qs = self.active().filter(release_date__gt=date_x, release_date__lte=datetime.now()).exclude(rent_flag=False).order_by('?')
        return qs

    def hottest_selling(self):
        date_x = datetime.now() - timedelta(60)
        return self.active().filter(
            release_date__lte=datetime.now(),
            release_date__gt=date_x,
            retail_price_new__gt=0,
            sold_amount__gt=0).order_by('-sold_amount', '-pk')


class ItemRentStatus:
    Unknown = 0
    NotReleased = 1
    High = 2
    Medium = 3
    Low = 4
    Available = 5
    NotRentable = 6

RENT_STATUS_CHOICES = (
    (ItemRentStatus.Unknown, 'Very Low'),
    (ItemRentStatus.NotReleased, 'Not Released'),
    (ItemRentStatus.High, 'High'),
    (ItemRentStatus.Medium, 'Medium'),
    (ItemRentStatus.Low, 'Low'),
    (ItemRentStatus.Available, 'Available'),
    (ItemRentStatus.NotRentable, 'Not Rentable'),
)


class Item(models.Model):
    class Meta:
        app_label = 'catalog'
        ordering = ['name']

    objects = ItemManager()

    upc = models.CharField(max_length=50, db_index=True, unique=True)
    bre_id = models.CharField(max_length=100, db_index=True, null=True, editable=False)
    bsid = models.CharField(max_length=20, db_index=True, null=True, editable=False)

    slug = models.SlugField(max_length=255, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    short_name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()

    number_of_players = models.SmallIntegerField(null=True, blank=True, db_index=True)
    number_of_online_players = models.SmallIntegerField(null=True, blank=True, db_index=True)

    release_date = models.DateField(db_index=True, null=True)

    category = models.ForeignKey(Category, related_name='items')
    type = models.ForeignKey(Type, null=True)
    rating = models.ForeignKey(Rating, null=True)
    publisher = models.ForeignKey(Publisher, null=True)
    game = models.ForeignKey(Game, null=True, editable=False)
    genres = models.ManyToManyField(Genre, null=True)
    tags = models.ManyToManyField(Tag, null=True)
    genre_list = models.CharField(max_length=1024, db_index=True, null=True, blank=True)
    tag_list = models.CharField(max_length=1024, db_index=True, null=True, blank=True)

    muze_cache = JSONField(null=True, editable=settings.DEBUG)
    votes = JSONField(null=True, editable=False)
    ratio = models.FloatField(default=0, editable=False, db_index=True)

    active = models.BooleanField(default=True, db_index=True)

    trade_flag = models.BooleanField(default=False, db_index=True)
    rent_flag = models.BooleanField(default=False, db_index=True)

    retail_price_new = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'), db_index=True)
    retail_price_used = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    trade_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'), db_index=True)
    trade_price_incomplete = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))

    base_retail_price_new = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    base_retail_price_used = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))
    base_trade_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=decimal.Decimal('0.0'))

    sold_amount = models.IntegerField(default=0, db_index=True)
    rent_amount = models.IntegerField(default=0, db_index=True)
    trade_amount = models.IntegerField(default=0, db_index=True)

    details_page_views = models.IntegerField(default=0, db_index=True)
    rent_status = models.IntegerField(default=0, choices=RENT_STATUS_CHOICES)

    game_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prebook_date = models.DateField(null=True, blank=True)
    pre_owned = models.BooleanField(default=False, db_index=True)

    ingram_code = models.CharField(max_length=20, null=True, db_index=True)
    top_rental = models.BooleanField(default=False, db_index=True)
    hot_trade = models.BooleanField(default=False, db_index=True)


    @staticmethod
    def search_by_keyword(keywords, qs=None):
        qs = qs or Item.objects.filter(active=True)
        if keywords:
            keywords = ' '.join(keywords.split())
            or_queries = []
            ff = ['name', 'short_name', 'upc', 'publisher__name', 'tag_list', 'genre_list']
            or_queries += [models.Q(**{x + '__icontains': keywords}) for x in ff]
            qs = qs.filter(reduce(operator.or_, or_queries))
            qs = qs.distinct('id')
        return qs

    def __unicode__(self):
        return self.name or self.short_name

    @models.permalink
    def get_absolute_url(self):
        return ('catalog:item', [self.slug, self.id])

    @staticmethod
    def list_by_category(category, genre=None):
        objects = Item.objects.filter(active=True, category=category, category__active=True)
        if genre:
            objects = objects.filter(genres=genre)
        return objects

    @staticmethod
    def list_all(genre=None, category=None):
        objects = Item.objects.filter(active=True, category__active=True)
        if genre:
            objects = objects.filter(genres=genre)
        if category:
            objects = objects.filter(category=category)
        return objects


    @staticmethod
    def list_new_releases(count=20):
        date_x = datetime.now() - timedelta(60)
        qs = Item.list_all().filter(release_date__gt=date_x, release_date__lte=datetime.now())
        if count is not None:
            qs = qs[:count]
        return qs


    @staticmethod
    def list_popular_by_publisher(publisher, count=12):
        return Item.list_all().filter(publisher=publisher).order_by('-ratio')[:count]


    @staticmethod
    def list_popular_by_category(category, count=12):
        return Item.list_all().filter(category=category).order_by('-ratio')[:count]


    @staticmethod
    def list_hottest_selling(category=None):
        return Item.list_all(category=category).filter(release_date__lte=datetime.now(),
                                                       retail_price_new__gt=0,
                                                       sold_amount__gt=0).order_by('-sold_amount', 'id')[:20]


    def is_pre_owned(self):
        from project.inventory.models import DistributorItem, Inventory
        if DistributorItem.objects.filter(item=self, is_new=False, quantity__gt=0).count() > 0:
            return True
        if Inventory.objects.filter(item=self, is_new=False, buy_only=True).count() > 0:
            return True
        return False

    def is_top_rental(self):
        return self.top_rental

    def is_rentable(self):
        return self.rent_status != ItemRentStatus.NotRentable


    def get_cropped_name(self, size=20):
        n = self.short_name
        if len(n) > size:
            n = n[:size-3].strip() + '...'
        return n

    def get_cropped_name_80(self):
        return self.get_cropped_name(80)

    def get_cropped_name_15(self):
        return self.get_cropped_name(15)

    def ratio_percents(self):
        return (self.ratio or 0) * 20


    def get_game_weight(self):
        return decimal.Decimal('%0.1f' % (self.game_weight or self.category.game_weight))


    def save(self, *args, **kwargs):
        if not self.votes:
            self.votes = {
                'total': 0,
                'amount': 0,
                'ratio': self.ratio,
                'details': [0, 0, 0, 0, 0]
            }
        #self.buy_new_flag = True if self.quantity_visco or self.quantity_jack or self.quantity_alpha else False
        super(Item, self).save(*args, **kwargs)


    def also_on(self):
        return Item.objects.filter(game=self.game).exclude(pk=self.pk)

    def get_ratio5(self):
        return int(round(self.ratio))
    ratio5 = property(get_ratio5)

    def recalc_votes(self, save=True):
        v = self.itemvote_set.all()
        res = v.aggregate(models.Sum('ratio'))
        total = int(res['ratio__sum'] or 0)
        amount = v.count()
        self.ratio = float(total) / amount if amount else 0
        self.votes = {
            'total': total,
            'amount': amount,
            'ratio': self.ratio,
            'details': [
                v.filter(ratio=1).count(),
                v.filter(ratio=2).count(),
                v.filter(ratio=3).count(),
                v.filter(ratio=4).count(),
                v.filter(ratio=5).count(),
            ]
        }
        if save:
            self.save()

    def get_trade_value_display(self):
        return '$%s' % self.trade_price if self.trade_price else 'Not Tradable'

    def list_similar_games(self, exclude_condition=None, count=24):
        if not exclude_condition:
            exclude_condition = {'pk': self.pk}

        if self.genres.count():
            return Item.objects.exclude(**exclude_condition).filter(category=self.category).extra(select={'weight': '''
                select count(1)
	              from catalog_item_genres G1, catalog_item_genres G2
	              where G1.genre_id = G2.genre_id
		              and G1.item_id = %d
		              and G2.item_id = catalog_item.id''' % self.pk}).order_by('-weight', 'name')[:count]
        else:
            return Item.list_by_category(self.category).exclude(**exclude_condition)[:count]

    def rent_games_like_this(self, count=24, user=None):
        at_home = list_games_at_home(user)
        exclude_pk = [self.pk] + map(lambda x: x.pk, at_home)
        return self.list_similar_games(exclude_condition={'pk__in': exclude_pk}, count=count)

    def list_popular_games(self, count=12):
        return Item.list_popular_by_category(self.category, count)

    def get_min_price(self):
        if self.pre_owned and self.retail_price_used > 0:
            return self.retail_price_used
        p = []
#        if self.available_for_selling_n() and self.retail_price_new > 0:
        if self.retail_price_new > 0:
            p.append(self.retail_price_new)
#        if self.available_for_selling_u() and self.retail_price_used > 0:
        if self.retail_price_used > 0:
            p.append(self.retail_price_used)
        if not p:
            return None
        return min(p)

    def margin(self):
        return self.base_retail_price_new - self.retail_price_new

    def genre_names(self):
        return map(lambda x: unicode(x), self.genres.all())

    def get_genres_display(self):
        return ', '.join(self.genre_names())

    @required_muze_cache('front_image')
    def get_front_image(self, suffix='jpg'):
        pk = str(self.pk)
        return pk[:2] + '/' + pk[2:4] + '/' + pk + '.' + suffix

    @required_muze_cache('screenshots')
    def get_screenshots(self):
        if settings.CATALOG_ITEM_SCREENSHOT_AMOUNT:
            return self.muze_cache['screenshots'][:settings.CATALOG_ITEM_SCREENSHOT_AMOUNT]
        else:
            return self.muze_cache['screenshots']

    @required_muze_cache('videos')
    def get_videos(self):
        if settings.CATALOG_ITEM_VIDEOS_AMOUNT:
            v = self.muze_cache['videos'][:settings.CATALOG_ITEM_VIDEOS_AMOUNT]
        else:
            v = self.muze_cache['videos']

        for vv in v:
            name, _ext = os.path.splitext(vv['file_name'])
            vv['thumb_url'] = settings.MEDIA_URL + 'thumbs/muze/Clip/' + name + '.jpg'
        return v

    @required_muze_cache('videos2')
    def get_videos2(self):
        if settings.CATALOG_ITEM_VIDEOS_AMOUNT:
            v = self.muze_cache['videos2'][:settings.CATALOG_ITEM_VIDEOS_AMOUNT]
        else:
            v = self.muze_cache['videos2']

#        v = [{'f1': 'GC/00/00/01/27/GC0000012708.flv',
#              'f2': 'GC/00/00/01/27/GC0000012743.flv',
#              'caption': ''},
#             {'f1': 'GC/00/00/14/31/GC0000143194.flv',
#              'f2': 'GC/00/00/14/30/GC0000143070.flv',
#              'caption': ''},]

        for vv in v:
            name, _ext = os.path.splitext(vv['f1'] or vv['f2'])
            vv['thumb_url'] = settings.MEDIA_URL + 'thumbs/muze/Clip/' + name + '.jpg'
        return v

    @required_muze_cache('expanded_description')
    def get_muze_description(self):
        return self.muze_cache['expanded_description']

    @required_muze_cache('msrp')
    def get_muze_msrp(self):
        if not self.muze_cache['msrp']:
            return None
        s = '%f' % (self.muze_cache['msrp'] or 0)
        s = s.split('.') + ['0']
        s = s[0] + '.' + s[1][:2]
        return decimal.Decimal(s)

    def get_catalog_grid_cover(self):
        if settings.DEBUG:
            img = ['1111175.png', '1111179.png', '1111232.png'][self.id % 3]
            return settings.STATIC_URL + 'img/debug/thumbs/covers/140x190/' + img

        image = self.get_front_image('png')
        return settings.MEDIA_URL + 'thumbs/covers/140x190/' + image if image else None

    def get_large_cover(self):
        image = self.get_front_image('png')
        return settings.MEDIA_URL + 'thumbs/covers/230x320/' + image if image else None

    def get_cover(self):
        if settings.DEBUG:
            img = ['103612.png', '104006.png', '104007.png'][self.id % 3]
            return settings.STATIC_URL + 'img/debug/thumbs/covers/170x220/' + img

        image = self.get_front_image('png')
        return settings.MEDIA_URL + 'thumbs/covers/170x220/' + image if image else None

    def get_thumb_image(self):
        image = self.get_front_image('png')
        return settings.MEDIA_URL + 'thumbs/covers/55x70/' + image if image else None

    def get_thumb_image2(self):
        image = self.get_front_image('png')
        return settings.MEDIA_URL + 'thumbs/covers/80x100/' + image if image else None

    def get_thumb_image3(self):
        if settings.DEBUG:
            img = ['100400.png', '100432.png', '100451.png'][self.id % 3]
            return settings.STATIC_URL + 'img/debug/thumbs/covers/120x160/' + img

        image = self.get_front_image('png')
        return settings.MEDIA_URL + 'thumbs/covers/120x160/' + image if image else None

    def get_nano_thumb(self):
        image = self.get_front_image('png')
        return settings.MEDIA_URL + 'thumbs/covers/37x47/' + image if image else None

    def get_retail_prices_display(self):
        today = datetime.now().date()
        if self.release_date > today:
            if not self.prebook_date or today < self.prebook_date:
                return '--'
        prices = []
#        if self.available_for_selling_n() and self.retail_price_new > 0:
        if self.retail_price_new > 0:
            prices.append(self.retail_price_new)
#        if self.available_for_selling_u() and self.retail_price_used > 0:
        if self.retail_price_used > 0:
            prices.append(self.retail_price_used)
        prices.sort()
        return mark_safe(' &ndash; '.join(map(lambda x: '$' + defaultfilters.floatformat(x, 2), prices)) or '--')

    def get_quantity_for_selling(self, is_new):
        from project.inventory.models import Inventory, InventoryStatus, DistributorItem
        from project.rent.models import RentOrder, RentOrderStatus
        from project.buy_orders.models import BuyOrderItem, BuyOrderItemStatus

        count = Inventory.objects.filter(item=self,
                                         status=InventoryStatus.InStock,
                                         dropship__code='FL',
                                         buy_only=True,
                                         is_new=is_new).count()
        iq = DistributorItem.objects.filter(item=self, is_new=is_new)
        if is_new:
            iq = iq.filter(distributor__id=5)
        count += iq.aggregate(Sum('quantity')).get('quantity__sum') or 0

        count -= RentOrder.objects.filter(item=self, status=RentOrderStatus.Pending).count()
        count -= BuyOrderItem.objects.filter(item=self, status__in=[BuyOrderItemStatus.Pending, BuyOrderItemStatus.Checkout]).count()
        return count

    def is_prereleased_game(self):
        return self.release_date > datetime.now().date() if self.release_date else True

    def is_out_of_stock(self, is_new):
        if is_new:
            return not self.available_for_selling_n()
        else:
            return not self.available_for_selling_u()

    def __available_for_selling(self, is_new):
        if is_new and self.is_prereleased_game():
            return 1 if self.retail_price_new else 0
        r = self.get_quantity_for_selling(is_new)
        return r if r > 0 else 0

    def available_for_selling(self, is_new=None):
        if is_new is None:
            return self.__available_for_selling(True) + self.__available_for_selling(False)
        else:
            return self.__available_for_selling(is_new)

    def available_for_selling_n(self):
        if self.retail_price_new:
            return self.available_for_selling(True)
        return False

    def available_for_selling_u(self):
        if self.retail_price_used:
            return self.available_for_selling(False)
        return False

    def get_trade_prices_display(self):
        if self.release_date > datetime.now().date():
            return 'Not Tradeable'
        if not self.trade_flag:
            return '--' #'Not Tradeable'
        return mark_safe(('$' + defaultfilters.floatformat(self.trade_price, 2)) if self.trade_price else '--')

    def get_trade_prices_display2(self):
        if self.release_date > datetime.now().date():
            return 'Not Tradeable'
        p = []
        if self.trade_price:
            p.append(self.trade_price)
        if self.trade_price_incomplete:
            p.append(self.trade_price_incomplete)
        if not self.trade_flag or not p:
            return '--' #'Not Tradeable'
        p.sort()
        p = map(lambda x: '$' + defaultfilters.floatformat(x, 2), p)
        return mark_safe('&nbsp;&ndash;&nbsp;'.join(p))

    def get_rent_status(self, user=None, short_na=False):
        if user:
            if is_item_on_list(self, user):
                return 'On List'
            if is_item_at_home(self, user):
                return 'At Home'
            if is_item_at_shipping_process(self, user):
                return 'Active'
        if short_na and self.rent_status in [1, 6]:
            return 'N/A'
        return self.get_rent_status_display()


    @staticmethod
    def find_by_upc(upc):
        qs = Item.objects.filter(upc=upc)
        if qs.count():
            return qs[0]
        else:
            return None

    def recalc_prices(self, prices=['retail_price_new', 'retail_price_used', 'trade_price'], save=True):
        dc = DiscountCalculator()

        if 'retail_price_new' in prices:
            if self.base_retail_price_new:
                discount = dc.ajdust_percent_new(self)
                price = self.base_retail_price_new
                value = price / decimal.Decimal('100.00') * discount
                self.retail_price_new = DiscountCalculator.round99(price + value)
            else:
                self.retail_price_new = decimal.Decimal('0.0')

        if 'retail_price_used' in prices:
            if self.base_retail_price_used:
                discount = dc.ajdust_percent_used(self)
                price = self.base_retail_price_used
                value = price / decimal.Decimal('100.00') * discount
                self.retail_price_used = DiscountCalculator.round99(price + value)
            else:
                self.retail_price_used = decimal.Decimal('0.0')

        if 'trade_price' in prices:
            if self.base_trade_price:
                discount = dc.adjust_trade_complete(self)
                price = self.base_trade_price
                value = price / decimal.Decimal('100.00') * discount
                self.trade_price = DiscountCalculator.round50(price + value)
                self.trade_price_incomplete = decimal.Decimal('%0.2f' % (self.trade_price * decimal.Decimal('0.75')))
            else:
                self.trade_price = decimal.Decimal('0.0')
                self.trade_price_incomplete = decimal.Decimal('0.0')
#            self.trade_flag = self.trade_price != decimal.Decimal('0.0')

        if save:
            self.save()

    def get_total_count(self):
        from project.inventory.models import Inventory
        return Inventory.objects.filter(item=self).count()

    def get_instock_count(self):
        from project.inventory.models import Inventory, InventoryStatus
        return Inventory.objects.filter(item=self, status=InventoryStatus.InStock).count()

    def get_unassigned_count(self):
        from project.inventory.models import Inventory
        return Inventory.objects.filter(item=self, dropship=None).count()

    def get_amount_instock_to_buy(self, is_new):
        from project.inventory.models import Inventory, InventoryStatus
#        from project.rent.models import RentOrder, RentOrderStatus
        from project.buy_orders.models import BuyOrderItem, BuyOrderItemStatus

        c = Inventory.objects.filter(item=self, status=InventoryStatus.InStock, dropship__code='FL', is_new=is_new, buy_only=True).count()
#        c -= RentOrder.objects.filter(status=RentOrderStatus.Pending, item=self).count()
        c -= BuyOrderItem.objects.filter(status=BuyOrderItemStatus.Pending, item=self).count()
        return c if c > 0 else 0

    def get_amount_from_distributor_to_buy(self, is_new):
        from project.inventory.models import DistributorItem
        if is_new:
            c = DistributorItem.objects.filter(item=self, is_new=is_new, distributor__id=5).aggregate(Sum('quantity'))
        else:
            c = DistributorItem.objects.filter(item=self, is_new=is_new).aggregate(Sum('quantity'))
        c = c.get('quantity__sum', 0) if c else 0
        return c if c else 0


class ItemViewsStat(models.Model):
    class Meta:
        app_label = 'catalog'
        ordering = ['-date']

    item = models.ForeignKey(Item)
    date = models.DateField(db_index=True)
    counter = models.IntegerField(default=0)

    @staticmethod
    @transaction.commit_on_success
    def inc(item, date=None, v=1):
        date = date or datetime.now().date()
        c = ItemViewsStat.objects.filter(item=item, date=date)
        if c:
            c = c[0]
            c.counter += v
            c.save()
        else:
            ItemViewsStat(item=item, date=date, counter=v).save()
