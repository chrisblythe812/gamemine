import decimal

from django.db import models
from django.core.cache import cache
from django_snippets.cache import simple_cached_call

from genres import Genre
from types import Type


class Category(models.Model):
    '''
    Defines catalog category
    '''
    
    class Meta:
        app_label = 'catalog'
        ordering = ['ordering', 'id']
        verbose_name_plural = 'categories'
    
    slug = models.SlugField(unique=True, editable=False, db_index=True)
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=100)
    ordering = models.SmallIntegerField(db_index=True, default=0, null=True)
    type = models.ForeignKey(Type)
    active = models.BooleanField(default=True, db_index=True)
    meta_title = models.CharField(max_length=500, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    bid = models.CharField(max_length=50)
    game_weight = models.DecimalField(max_digits=5, decimal_places=1, default=decimal.Decimal('6.0')) 

    
    @staticmethod
    def clear_cache():
        cache.delete_many([
            'catalog/category/list_names',
            'catalog/category/list_slugs',
        ])
        

    @staticmethod
    def list():
        "Returns a list of all categories"
        return Category.objects.filter(active=True);
    
    
    @staticmethod
    @simple_cached_call('catalog/category/list_names')
    def list_names():
        "Returns a list of slug-name pairs"
        return [(c.slug, c.name, c.description) for c in Category.list()]
    
    
    @staticmethod
    @simple_cached_call('catalog/category/list_slugs')
    def list_slugs():
        "Returns a list of slugs"
        return [c.slug for c in Category.list()]

    def list_top_trades(self, amount=8):
        return self.items.filter(active=True, trade_flag=True).order_by('-trade_price')[:amount]
    
    @models.permalink
    def get_absolute_url(self):
        return ('catalog:category', [self.slug])


    def __unicode__(self):
        return self.name or self.description


    def save(self, *args, **kwargs):
        Category.clear_cache()
        super(Category, self).save(*args, **kwargs)

    
    def list_genres(self):
        return Genre.objects.filter(type=self.type)
