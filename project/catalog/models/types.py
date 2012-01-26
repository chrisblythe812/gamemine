from django.db import models


class Type(models.Model):
    '''
    Describes types of items
    '''
    class Meta:
        app_label = 'catalog'
        ordering = ['id']

    name = models.CharField(max_length=50, unique=True)
    plural_name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.name
