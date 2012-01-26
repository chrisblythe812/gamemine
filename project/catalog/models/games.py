from django.db import models


class Game(models.Model):
    class Meta:
        app_label = 'catalog'
        ordering = ['id']

    name = models.CharField(max_length=100, db_index=True, unique=True)

    def __unicode__(self):
        return self.name
