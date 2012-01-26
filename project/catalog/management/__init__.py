from django.db.models.signals import post_syncdb
from django.core.management import call_command

import project.catalog.models
from project.catalog.models import Category


def add_stuff(sender, **kwargs):
    if not Category.objects.count():
        call_command("loaddata", "types.yaml")
        call_command("loaddata", "genres.yaml")
        call_command("loaddata", "tags.yaml")
        call_command("loaddata", "games.json")
        call_command("loaddata", "publishers.yaml")
        call_command("loaddata", "ratings.yaml")
        call_command("loaddata", "categories.yaml")
        call_command("loaddata", "items.json")

post_syncdb.connect(add_stuff, sender=project.catalog.models)
