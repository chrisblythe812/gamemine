from django.db import models

from types import Type


class Genre(models.Model):
    '''
    Describes types of items
    '''
    class Meta:
        app_label = 'catalog'
        ordering = ['type', 'ordering', 'name']
        unique_together = ('name', 'type')

    name = models.CharField(max_length=50, db_index=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    type = models.ForeignKey(Type, null=True, blank=True)
    ordering = models.SmallIntegerField(db_index=True, null=True)
    
    def __unicode__(self):
        return self.description or self.name

    def get_absolute_url(self):
        return '#'
