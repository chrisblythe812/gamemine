from django.db.models.signals import post_syncdb
from django.core.management import call_command

import project.rent.models
from project.rent.models import BaseRentalPlan, AllocationFactor


def add_rental_plans(sender, **kwargs):
    if not BaseRentalPlan.objects.count():
        call_command("loaddata", "baserentalplans.json")
        call_command("loaddata", "new_baserentalplans.json")
    if not AllocationFactor.objects.count():
        call_command("loaddata", "allocation_factors.json")

post_syncdb.connect(add_rental_plans, sender=project.rent.models)
