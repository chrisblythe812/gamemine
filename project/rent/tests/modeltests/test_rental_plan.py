from django.test import TestCase

from project.rent.models import RentalPlan


class RentalPlanTestCase(TestCase):
    def test_rental_plan(self):
        self.assertTrue(RentalPlan._RentalPlan__get(0))
