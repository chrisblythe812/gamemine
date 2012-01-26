import decimal
from logging import debug #@UnusedImport

from django.db import models


class CommonValues(models.Model):
    class Meta:
        verbose_name_plural = 'common values'
    
    name = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    
    def __unicode__(self):
        return self.name
    
class CategoryDiscount(models.Model):
    class Meta:
        ordering = ['category__ordering']
    
    category = models.ForeignKey('catalog.Category', unique=True)
    ajdust_percent_new = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    ajdust_percent_used = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    adjust_trade_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_price_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_credit = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))

    def __unicode__(self):
        return unicode(self.category)

class GenreDiscount(models.Model):
    class Meta:
        ordering = ['genre__type', 'genre__ordering', 'genre__name']

    genre = models.ForeignKey('catalog.Genre', unique=True)
    ajdust_percent_new = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    ajdust_percent_used = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    adjust_trade_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_price_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_credit = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))

    def __unicode__(self):
        return unicode(self.genre)

class TagDiscount(models.Model):
    tag = models.ForeignKey('catalog.Tag', unique=True)
    ajdust_percent_new = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    ajdust_percent_used = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    adjust_trade_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_price_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_credit = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))

    def __unicode__(self):
        return unicode(self.tag)


class GroupDiscount(models.Model):
    name = models.CharField(max_length=50, db_index=True, unique=True)
    ajdust_percent_new = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    ajdust_percent_used = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    adjust_trade_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_price_complete = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    trade_credit = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.0'))
    items = models.ManyToManyField('catalog.Item')

    def __unicode__(self):
        return unicode(self.name)



class DiscountCalculator:
    def __init__(self):
        pass
    
    @staticmethod
    def round99(val):
        t = val.as_tuple()
        i2 = int((''.join(str(i) for i in t.digits[t.exponent:]) + '00')[:2])
        i1 = int(val)
        if i2 < 50:
            i1-=1
        return decimal.Decimal('%d.99' % i1)
    
    @staticmethod
    def round50(val):
        t = val.as_tuple()
        i2 = int((''.join(str(i) for i in t.digits[t.exponent:]) + '00')[:2])
        i1 = int(val)
        if i2 < 50:
            i2 = 0
        elif i2 > 50:
            i1 += 1
            i2 = 0
        return decimal.Decimal('%d.%d' % (i1, i2))
        
    @property
    def common_values(self):
        if hasattr(self, '_common_values'):
            return self._common_values
        self._common_values = {}
        for i in CommonValues.objects.all():
            self._common_values[i.name.lower()] = i.value
        return self._common_values

    @property
    def category_discount(self):
        if hasattr(self, '_category_discount'):
            return self._category_discount
        self._category_discount = {}
        for i in CategoryDiscount.objects.all():
            self._category_discount[i.category_id] = i
        return self._category_discount

    @property
    def genre_discount(self):
        if hasattr(self, '_genre_discount'):
            return self._genre_discount
        self._genre_discount = {}
        for i in GenreDiscount.objects.all():
            self._genre_discount[i.genre_id] = i
        return self._genre_discount

    @property
    def tag_discount(self):
        if hasattr(self, '_tag_discount'):
            return self._tag_discount
        self._tag_discount = {}
        for i in TagDiscount.objects.all():
            self._tag_discount[i.tag_id] = i
        return self._tag_discount

    @property
    def group_discount(self):
        if hasattr(self, '_group_discount'):
            return self._group_discount
        self._group_discount = {}
        for i in GroupDiscount.objects.all():
            for j in i.items.all():
                self._group_discount[j.id] = i
        return self._group_discount

    def ajdust_percent_new(self, item):
        val = decimal.Decimal('0.0')
        if u'retail_price_new' in self.common_values:
            v =  self.common_values[u'retail_price_new']
            if v: val = v
        if item.category_id in self.category_discount:
            v = self.category_discount[item.category_id].ajdust_percent_new
            if v: val = v
        for g in item.genres.all():
            if g.id in self.genre_discount:
                v = self.genre_discount[g.id].ajdust_percent_new
                if v: 
                    val = v
                    break
        for t in item.tags.all():
            if t.id in self.tag_discount:
                v = self.tag_discount[t.id].ajdust_percent_new
                if v: 
                    val = v
                    break
        if item.id in self.group_discount:
            v = self.group_discount[item.id].ajdust_percent_new
            if v: val = v
        return val

        
    def ajdust_percent_used(self, item):
        val = decimal.Decimal('0.0')
        if u'retail_price_new' in self.common_values:
            v =  self.common_values[u'retail_price_used']
            if v: val = v
        if item.category_id in self.category_discount:
            v = self.category_discount[item.category_id].ajdust_percent_used
            if v: val = v
        for g in item.genres.all():
            if g.id in self.genre_discount:
                v = self.genre_discount[g.id].ajdust_percent_used
                if v: 
                    val = v
                    break
        for t in item.tags.all():
            if t.id in self.tag_discount:
                v = self.tag_discount[t.id].ajdust_percent_used
                if v: 
                    val = v
                    break
        if item.id in self.group_discount:
            v = self.group_discount[item.id].ajdust_percent_used
            if v: val = v
        return val

    
    def adjust_trade_complete(self, item):
        val = decimal.Decimal('0.0')
        if u'retail_price_new' in self.common_values:
            v =  self.common_values[u'trade_price_complete']
            if v: val = v
        if item.category_id in self.category_discount:
            v = self.category_discount[item.category_id].adjust_trade_complete
            if v: val = v
        for g in item.genres.all():
            if g.id in self.genre_discount:
                v = self.genre_discount[g.id].adjust_trade_complete
                if v: 
                    val = v
                    break
        for t in item.tags.all():
            if t.id in self.tag_discount:
                v = self.tag_discount[t.id].adjust_trade_complete
                if v: 
                    val = v
                    break
        if item.id in self.group_discount:
            v = self.group_discount[item.id].adjust_trade_complete
            if v: val = v
        return val
        