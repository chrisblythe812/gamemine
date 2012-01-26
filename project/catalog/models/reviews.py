import datetime

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
from django.core import urlresolvers


COMMENT_MAX_LENGTH = getattr(settings,'COMMENT_MAX_LENGTH',3000)


class Review(models.Model):
    class Meta:
        app_label = 'catalog'
        ordering = ('-helpful_index', '-timestamp', )

    content_type = models.ForeignKey(ContentType, related_name="content_type_set_for_%(class)s", editable=False)
    object_pk = models.TextField(editable=False)
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")
    site = models.ForeignKey(Site, editable=False)

    user = models.ForeignKey(User)
    title = models.CharField(max_length=300, null=True,)
    comment = models.TextField(max_length=COMMENT_MAX_LENGTH)
    rating = models.SmallIntegerField(choices=[[x, x] for x in range(1, 6)])
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    ip_address = models.IPAddressField(blank=True, null=True)
    
    helpful_index = models.IntegerField(db_index=True, default=0)


    def __unicode__(self):
        txt = self.title or self.comment
        txt = txt[:47] + '...' if len(txt) > 47 else txt
        return "%s: %s" % (self.user, txt)
    
    def get_synopsis(self):
        return self.comment[:47] + '...' if len(self.comment) > 47 else self.comment
    synopsis = property(get_synopsis)

    def get_content_object_url(self):
        """
        Get a URL suitable for redirecting to the content object.
        """
        return urlresolvers.reverse(
            "comments-url-redirect",
            args=(self.content_type_id, self.object_pk)
        )
        
    def get_user_email(self):
        return self.user.email if self.user else None
    user_email = property(get_user_email)
    
    def get_date(self):
        return self.timestamp.date()
    date = property(get_date)

    @staticmethod
    def get_for_object(object):
        return Review.objects.filter(content_type=ContentType.objects.get_for_model(object), 
                                     object_pk=object.pk)

    @staticmethod
    def get_helpful(object):
        return Review.objects.filter(content_type=ContentType.objects.get_for_model(object), 
                                     object_pk=object.pk, helpful_index__gt=0).order_by('-helpful_index')
        
    def vote_for_review(self, user, vote):
        o, _c = ReviewHelpfulVote.objects.get_or_create(user=user, review=self)
        o.vote = vote
        o.save()
        
    def recalc_helpful_index(self, save=True):
        self.helpful_index = ReviewHelpfulVote.objects.filter(review=self).aggregate(models.Sum('vote'))['vote__sum']
        if save:
            self.save()
        

class ReviewHelpfulVote(models.Model):
    class Meta:
        app_label = 'catalog'
    user = models.ForeignKey(User)
    review = models.ForeignKey(Review)
    vote = models.IntegerField(default=0)


def update_votes_index(sender, instance, created, **kwargs):
    instance.review.recalc_helpful_index()
models.signals.post_save.connect(update_votes_index, ReviewHelpfulVote)
