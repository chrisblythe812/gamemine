from django.db import models

from types import Type


class Rating(models.Model):
    class Meta:
        app_label = 'catalog'
        ordering = ['type', 'title']
        unique_together = (('type', 'title'),)

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True, blank=True)
    type = models.ForeignKey(Type)
    esrb_symbol = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    image = models.ImageField(upload_to='rating', null=True, blank=True)

    def __unicode__(self):
        return self.title or self.description
