from django.db.models.signals import post_syncdb
from django.core.management import call_command

import project.taxes.models
from project.taxes.models import ByCountyTax


def add_taxes(sender, **kwargs):
    if not ByCountyTax.objects.count():
        call_command("loaddata", "taxes.json")

post_syncdb.connect(add_taxes, sender=project.taxes.models)
