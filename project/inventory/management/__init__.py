from django.db.models.signals import post_syncdb
from django.core.management import call_command

import project.inventory.models
from project.inventory.models import Dropship


def add_dropships(sender, **kwargs):
    if not Dropship.objects.count():
        call_command("loaddata", "dropships.yaml")
        call_command("loaddata", "inventories.json")

post_syncdb.connect(add_dropships, sender=project.inventory.models)
