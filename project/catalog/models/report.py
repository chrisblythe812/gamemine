from django.db import models

TYPES = (
    ('New Inventory and Price', 'New Inventory and Price'), 
    ('Used inventory and Price', 'Used inventory and Price'), 
    ('Used Price and Trade Values', 'Used Price and Trade Values'), 
)

class ReportUpload(models.Model):
    '''
    Defines catalog category
    '''
    class Meta:
        app_label = 'catalog'
        ordering = ['-created']
        verbose_name_plural = 'Report Upload'
    
    created = models.DateTimeField(db_index=True)
    type = models.CharField(max_length=100, choices=TYPES)
    report = models.TextField()
    source = models.TextField()
    unknown_upc = models.TextField()
    unknown_upc_count = models.IntegerField()
    
    def __unicode__(self):
        return unicode(self.created)

