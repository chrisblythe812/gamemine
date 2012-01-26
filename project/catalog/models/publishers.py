from django.core.urlresolvers import reverse
from django.db import models
from django.utils.http import urlquote

from types import Type


class Publisher(models.Model):
    '''
    Describes publishers
    '''
    class Meta:
        app_label = 'catalog'
        ordering = ['id']
        unique_together = (('name', 'type'),)

    name = models.CharField(max_length=150, db_index=True)
    description = models.TextField(null=True, blank=True)
    type = models.ForeignKey(Type, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('search:search') + '?publisher=' + urlquote(self.name)
