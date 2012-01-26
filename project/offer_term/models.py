from django.db import models
from tinymce import models as tinymce_models

class OfferTerm(models.Model):
    BUY = 1
    TRADE = 2
    TYPE = ((BUY,'Buy'),(TRADE,'Trade'),)
    class Meta:
        verbose_name = 'Offer Term'
        verbose_name_plural = 'Offer Terms'
    type = models.IntegerField(choices=TYPE,unique=True)
    text = tinymce_models.HTMLField()    
    def __unicode__(self):
        return self.get_type_display()
    