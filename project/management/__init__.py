from django.db.models.signals import post_syncdb
from django.core.management import call_command

import django.contrib.sites.models
from django.contrib.sites.models import Site


def add_site(sender, **kwargs):
    Site.objects.filter(domain="example.com").update(domain="localhost:8000", name="gamemine.com")

post_syncdb.connect(add_site, sender=django.contrib.sites.models)
