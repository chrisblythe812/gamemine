from django.test import TestCase

from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.tests.regressiontests.add_item import AddItemTestCase
from project.new_rent.models import RentalPlan
from project.catalog.models.items import Item
from project.rent.models import RentList


class AddItemTests(TestCase, AddItemTestCase, SignUpTestCase):
    def test_add_item_to_rentlist(self):
        item = Item.objects.all()[0]
        self.signup_plan(RentalPlan.objects.get(slug="unlimited1"))
        self.add_item_to_rentlist(item)

        self.assertEqual(RentList.objects.count(), 1)
