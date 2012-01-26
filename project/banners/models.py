import random

from django.db import models

from project.catalog.models import Item, Category


class Targets:
    All = 0
    Members = 1
    NonMembers = 2


TARGET_CHOICES = (
    (Targets.All, 'All users'),
    (Targets.Members, 'Members only'),
    (Targets.NonMembers, 'Non-Members only'),
)


class FeaturedGame(models.Model):
    category = models.ForeignKey(Category, null=True, blank=True)
    game = models.ForeignKey(Item, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='featured-games')
    active = models.BooleanField(db_index=True, default=True)
    link_class = models.CharField(max_length=255, null=True, blank=True)
    targets = models.IntegerField(choices=TARGET_CHOICES, default=Targets.All, db_index=True)

    @staticmethod
    def get(category=None, request=None):
        b = FeaturedGame.objects.filter(active=True).filter(category=category)
        if request:
            if request.user.is_authenticated():
                b = b.filter(targets__in=[Targets.All, Targets.Members])
            else:
                b = b.filter(targets__in=[Targets.All, Targets.NonMembers])
        b = list(b)
        if not b:
            return None
        random.seed()
        random.shuffle(b)
        return b[:3]

    def __unicode__(self):
        if self.game:
            return '%s %s' % (self.game, self.category)
        if self.url:
            return '%s %s' % (self.url, self.category)
        return '/ %s' % self.category

    def get_absolute_url(self):
        if self.game:
            return self.game.get_absolute_url()
        if self.url:
            return self.url
        return '/'


class CatalogBanner(models.Model):
    url = models.CharField(max_length=255)
    image = models.ImageField(upload_to='catalog-banners')
    active = models.BooleanField(db_index=True, default=True)

    @staticmethod
    def get():
        b = CatalogBanner.objects.filter(active=True)
        b = list(b)
        if not b:
            return None
        random.seed()
        random.shuffle(b)
        return b[:3]

    def get_absolute_url(self):
        return self.url

LISTS = (
    (1, 'Buy List'),
    (2, 'Trade List'),
    (3, 'Rent List'),
)


class ListPageBannerManager(models.Manager):
    def get_random(self, lst=None, count=1):
        banners = self.filter(active=True).order_by('?')
        if lst:
            banners = banners.filter(list=lst)
        banners = banners[:count]
        if banners.count() == 1:
            return banners[0]


class ListPageBanner(models.Model):
    list = models.IntegerField(choices=LISTS, null=True, blank=True)
    game = models.ForeignKey(Item)
    image = models.ImageField(upload_to='lists-banners')
    active = models.BooleanField(db_index=True, default=True)

    def get_absolute_url(self):
        return self.game.get_absolute_url()

    objects = ListPageBannerManager()
