import sys
import logging
import itertools
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import LabelCommand
from django.db.models.aggregates import Sum
from django.db import connection

from project.catalog.models import Item
from project.buy_orders.models import BuyOrderItem, BuyOrderStatus, BuyList
from project.rent.models import RentOrder, RentList
from project.trade.models import TradeOrderItem
from project.catalog.models.reviews import Review
from project.catalog.models.item_votes import ItemVote
from project.catalog.models.items import ItemRentStatus, ItemViewsStat
from project.inventory.models import Inventory, DistributorItem
import decimal

info = logging.getLogger('crontab').info
error = logging.getLogger('crontab').error
debug = logging.getLogger('crontab').debug
warn = logging.getLogger('crontab').warn


class Command(LabelCommand):
    args = '<fix_counters, update_rent_status, update_caches>'
    help = 'Working with catalog'
    label = 'command'

    def handle_label(self, label, **options):
        if label == 'update_caches':
            self.do_update_caches()
        elif label == 'fix_counters':
            self.do_fix_counters()
        elif label == 'recalc_votes':
            self.do_recalc_votes()
        elif label == 'update_rent_status':
            self.do_update_rent_status()
        elif label == 'recalc_prices':
            self.do_recalc_prices()
        elif label == 'fix_stats':
            self.do_fix_stats()
        elif label == 'load_prices':
            self.do_load_prices()

    def do_update_caches(self):
        print 'Updating items cache...'
        items = Item.objects.all().select_related()
        count = items.count()
        for item, i in itertools.izip(items, itertools.count(1)):
            if i % 100 == 0:
                print 'Processed %d items of %d...' % (i, count)
            item.tag_list = ' '.join(map(lambda x: x.name, item.tags.all()))
            item.genre_list = ' '.join(map(lambda x: x.name, item.genres.all()))
            item.save()
            if i % 100 == 0:
                print item.tag_list

    def do_fix_counters(self):
        print 'Fixing pre_owned flag...'
        cursor = connection.cursor()  #@UndefinedVariable
        cursor.execute("update catalog_item set pre_owned='f'")
        for i in Inventory.objects.filter(is_new=False, buy_only=True, item__retail_price_used__gt=0):
            i.item.pre_owned = True
            i.item.save()
        for i in DistributorItem.objects.filter(is_new=False, quantity__gt=0, item__retail_price_used__gt=0):
            i.item.pre_owned = True
            i.item.save()
        for i in Item.objects.filter(pre_owned=True):
            if not i.available_for_selling_u():
                i.pre_owned = False
                i.save()
        print 'Fixing top_rental flag...'
        cursor.execute("update catalog_item set top_rental='f'")
        for i in Item.objects.filter(rent_amount__gt=0, rent_flag=True).exclude(rent_status=ItemRentStatus.NotRentable).order_by('-rent_amount')[:100]:
            i.top_rental = True
            i.save()

        print 'Fixing hot_trade flag...'
        cursor.execute("update catalog_item set hot_trade='f'")
        for i in Item.objects.filter(trade_amount__gt=0, trade_flag=True)[:100]:
            i.hot_trade = True
            i.save()

        print 'Fixing sold/rented/traded counters...'
        date_x = datetime.now() - timedelta(90)
        for item in Item.objects.all():
            item.sold_amount = BuyOrderItem.objects.filter(item=item, order__create_date__gte=date_x).exclude(order__status=BuyOrderStatus.New).count()
            item.sold_amount *= 1000000
            item.sold_amount += 10000 * BuyList.objects.filter(item=item, added__gte=date_x).count()
            item.sold_amount += ItemViewsStat.objects.filter(item=item, date__gte=date_x).aggregate(Sum('counter'))['counter__sum'] or 0

            item.rent_amount = RentOrder.objects.filter(item=item, date_rent__gte=date_x).count()
            item.rent_amount += RentList.objects.filter(item=item, added__gte=date_x).count()

            item.trade_amount = TradeOrderItem.objects.filter(item=item, processed_date__gte=date_x).count()

            item.save()

    def do_recalc_votes(self):
        print 'Updating votes...'
        for r in Review.objects.all():
            if ItemVote.objects.filter(review=r).count() == 0:
                ItemVote(
                    item=r.content_object,
                    timestamp=r.timestamp,
                    user=r.user,
                    review=r,
                    ratio=r.rating,
                    ip_address=r.ip_address,
                ).save()
        items = Item.objects.all().select_related()
        count = items.count()
        for item, i in itertools.izip(items, itertools.count(1)):
            if i % 100 == 0:
                print 'Recalculating ratings: %d items out of %d...' % (i, count)
            item.recalc_votes()

    def do_update_rent_status(self):
        def get_status(item):
            rd = item.release_date or (datetime.now() + timedelta(1)).date()
            if rd > datetime.now().date():
                return ItemRentStatus.NotReleased

            if not item.rent_flag:
                return ItemRentStatus.NotRentable

            from project.inventory.models import InventoryStatus
            count = Inventory.objects.filter(item=item, status__in=[InventoryStatus.InStock, InventoryStatus.Available]).exclude(buy_only=True).count()
#            count += DistributorItem.objects.filter(item=item).aggregate(Sum('quantity'))['quantity__sum'] or 0
            rented_count = Inventory.objects.filter(item=item, status__in=[InventoryStatus.Pending, InventoryStatus.Rented]).exclude(buy_only=True).count()
            if count == 0 and rented_count == 0: # There is no available inventory of the game in stock.
                return ItemRentStatus.Unknown

            wanted_by = RentList.objects.filter(item=item).count() or 1

            rent_status_percent = 100 * count / wanted_by
            if rent_status_percent >= 100:
                return ItemRentStatus.Available
            elif rent_status_percent >= 75: # The game has fewer copies than requests available and wait is 1 to 3 days (75%).
                return ItemRentStatus.High
            if rent_status_percent >= 50: # The game is in high demand and the wait is 4 to 6 days (50%-74%).
                return ItemRentStatus.Medium
#            if rent_status_percent >= 25: # The game is in very high demand and the wait is 7 to 10 days (25%-49%).
            return ItemRentStatus.Low

        info('Recalculating rent statuses...', extra={'url': 'task://catalog/update_rent_status'})
        items = Item.objects.all().select_related()
        _count = items.count()
        for item, _i in itertools.izip(items, itertools.count(1)):
#            if i % 100 == 0:
#                print 'Processed %d items of %d...' % (i, count)
            try:
                item.rent_status = get_status(item)
                item.save()
            except Exception, _e:
                error('Error occurs when processing item %s', item.id,
                      exc_info=sys.exc_info(), extra={'url': item.get_absolute_url()})
        info('Rent statuses were successfully recalculated', extra={'url': 'task://catalog/update_rent_status'})

    def do_recalc_prices(self):
        debug('Recalculating prices statuses...')
        items = Item.objects.all().select_related()
        count = items.count()
        for item, i in itertools.izip(items, itertools.count(1)):
            if i % 100 == 0:
                print 'Processed %d items of %d...' % (i, count)
            item.recalc_prices()
            item.save()

    def do_fix_stats(self):
        def update(item, v, days):
            for x in range(days):
                date = (datetime.now() - timedelta(x)).date()
                ItemViewsStat.inc(item, date, v)

        ItemViewsStat.objects.all().delete()
        items = Item.objects.filter(details_page_views__gt=0).order_by('-details_page_views')
        for i in items:
            days = 90
            v = (Decimal(str(i.details_page_views)) / 90)
            if v < 0.3:
                v = 0
            elif v < 0.5:
                days = 30
                v = 1
            else:
                v = int('%0.0f' % v)
            if v:
                update(i, v, days)

    def do_load_prices(self):
        sys.stdin.readline()
        for l in sys.stdin:
            l = l.strip().split('\t')
            p = l[-1].strip('$')
            item = Item.objects.get(upc=l[0])
            item.retail_price_used = decimal.Decimal(p)
            if not item.active:
                print item.upc
            item.save()
