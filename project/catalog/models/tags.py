from logging import debug #@UnusedImport

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.http import urlquote


class Tag(models.Model):
    class Meta:
        app_label = 'catalog'
        ordering = ['name']

    name = models.CharField(max_length=50, unique=True, db_index=True)
    
    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('search:search') + '?tag=' + urlquote(self.name)
