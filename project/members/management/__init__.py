from django.db.models.signals import post_syncdb
from django.core.management import call_command

import project.members.models
from project.members.models import Campaign


def add_campaigns(sender, **kwargs):
    if not Campaign.objects.count():
        call_command("loaddata", "campaigns.json")

post_syncdb.connect(add_campaigns, sender=project.members.models)
