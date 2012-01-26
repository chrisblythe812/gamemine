from logging import debug #@UnusedImport

from django.db import models
from django.contrib.localflavor.us.models import USStateField
import decimal

class CountyManager(models.Manager):
    def get_by_natural_key(self, state, name):
        return self.get(state=state, name=name)


class County(models.Model):
    class Meta:
        unique_together = (('state', 'name'), )
        verbose_name_plural = 'Counties'
        ordering = ['state', 'name']


    objects = CountyManager()

    state = USStateField(db_index=True)
    name = models.CharField(max_length=50, null=True)

    def natural_key(self):
        return (self.state, self.name)

    def __unicode__(self):
        return '%s, %s' % (self.state, self.name)


class Tax(models.Model):
    class Meta:
        abstract = True

    value = models.DecimalField(max_digits=12, decimal_places=4)

    @staticmethod
    def get_value(state, county=None):
        if not state:
            return decimal.Decimal('0.0')
        try:
            county = County.objects.get(state=state, name=county)
        except:
            county = None
        if county:
            try:
                return ByCountyTax.objects.get(county=county).value
            except:
                pass # nothin' to do. just pass through
        try:
            return ByStateTax.objects.get(state=state).value
        except:
            return decimal.Decimal('0.0')


class ByCountyTax(Tax):
    class Meta:
        ordering = ['county__state', 'county__name']

    county = models.OneToOneField(County)


class ByStateTax(Tax):
    class Meta:
        ordering = ['state', ]

    state = USStateField(db_index=True, unique=True)
