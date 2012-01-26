import random
from django.db import models
from project.members.models import Campaign

_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def random_string(length):
    return ''.join([random.choice(_LETTERS) for _x in xrange(length)])

class Subscriber(models.Model):
    email = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)
    guid = models.CharField(max_length=32)
    campaign_cid = models.CharField(max_length=20, null=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.guid:
            self.guid = random_string(32)
        super(Subscriber, self).save(*args, **kwargs)

    def get_campaign_cid_display(self):
        if self.campaign_cid is None or self.campaign_cid==u'':
            return u"Gamemine Direct"
        try:
            return Campaign.objects.get(pk=self.campaign_cid).name
        except:
            return u"Unknown Campaign"

