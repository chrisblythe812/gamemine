import datetime

from django import forms
from django.contrib.comments.forms import CommentSecurityForm
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode


COMMENT_MAX_LENGTH = getattr(settings,'COMMENT_MAX_LENGTH', 3000)


class ReviewForm(CommentSecurityForm):
    title = forms.CharField(required=False, max_length=300)
    comment = forms.CharField(widget=forms.Textarea, max_length=COMMENT_MAX_LENGTH)
    rating = forms.ChoiceField(choices=[(x, x) for x in range(5, 0, -1)])
    

    def get_comment_object(self):
        """
        Return a new (unsaved) comment object based on the information in this
        form. Assumes that the form is already validated and will throw a
        ValueError if not.

        Does not set any of the fields that would come from a Request object
        (i.e. ``user`` or ``ip_address``).
        """
        if not self.is_valid():
            raise ValueError("get_comment_object may only be called on valid forms")

        CommentModel = self.get_comment_model()
        new = CommentModel(**self.get_comment_create_data())
        new = self.check_for_duplicate_comment(new)

        return new

    def get_comment_model(self):
        # Use our custom comment model instead of the built-in one.
        from project.catalog.models import Review
        return Review

    def get_comment_create_data(self):
        title = self.cleaned_data["title"]
        if title.upper() == 'SUBJECT...':
            title = ''
        return dict(
            content_type = ContentType.objects.get_for_model(self.target_object),
            object_pk    = force_unicode(self.target_object._get_pk_val()),
            title        = title,
            comment      = self.cleaned_data["comment"],
            rating       = self.cleaned_data["rating"],
            site_id      = settings.SITE_ID,
            timestamp    = datetime.datetime.now(),
        )

    def check_for_duplicate_comment(self, new):
        """
        Check that a submitted comment isn't a duplicate. This might be caused
        by someone posting a comment twice. If it is a dup, silently return the *previous* comment.
        """
        possible_duplicates = self.get_comment_model()._default_manager.using(
            self.target_object._state.db
        ).filter(
            content_type = new.content_type,
            object_pk = new.object_pk,
        )
        for old in possible_duplicates:
            if old.timestamp.date() == new.timestamp.date() and old.comment == new.comment:
                return old

        return new
