from logging import debug #@UnusedImport
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.comments.signals import comment_was_posted 

from items import Item
from reviews import Review


class ItemVote(models.Model):
    class Meta:
        app_label = 'catalog'
    
    item = models.ForeignKey(Item)
    ratio = models.SmallIntegerField(choices=[[x, x] for x in range(1, 6)])
    timestamp = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey(User, null=True)
    ip_address = models.IPAddressField(null=True)
    review = models.OneToOneField(Review, null=True)
    
    def save(self, *args, **kwargs):
        super(ItemVote, self).save(*args, **kwargs)
        self.item.recalc_votes(True)


def handle_new_comment(comment, request, *args, **kwargs):
    if ItemVote.objects.filter(review=comment).count():
        return
    ItemVote(item=comment.content_object,
             ratio=comment.rating,
             user=comment.user,
             ip_address=comment.ip_address,
             review=comment).save()
comment_was_posted.connect(handle_new_comment)

def do_recalc(sender, instance, **kwargs):
    instance.item.recalc_votes(True)
models.signals.post_delete.connect(do_recalc, ItemVote)
models.signals.post_save.connect(do_recalc, ItemVote)
