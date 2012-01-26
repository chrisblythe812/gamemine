from django.utils.unittest import TestCase, main
from decimal import Decimal
from datetime import datetime
from models import RentalPlan


class Tests(TestCase):
    def _do_test(self, plan, payments):
        plan_start_date, first_payment_amount = payments[0]
        self.assertEqual(RentalPlan.get_start_payment_amount(plan), Decimal(first_payment_amount))
        last_payment_date = plan_start_date
        for p in payments[1:]:
            last_payment_date, amount = RentalPlan.get_next_payment(plan, plan_start_date, last_payment_date)
            self.assertEqual(last_payment_date, p[0])
            self.assertEqual(amount, Decimal(p[1]))

    def test_plans_a(self):
        self._do_test(RentalPlan.PlanA, (
                (datetime(2010, 1, 1),  '8.99'),
                (datetime(2010, 2, 1),  '8.99'),
                (datetime(2010, 3, 1),  '8.99'),
                (datetime(2010, 4, 1),  '8.99'),
                (datetime(2010, 5, 1),  '8.99'),
                (datetime(2010, 6, 1),  '8.99'),
                (datetime(2010, 7, 1),  '8.99'),
                (datetime(2010, 8, 1),  '8.99'),
                (datetime(2010, 9, 1),  '8.99'),
                (datetime(2010, 10, 1), '8.99'),
            ))

    def test_plans_b(self):
        self._do_test(RentalPlan.PlanB, (
                (datetime(2010, 1, 1),  '13.99'),
                (datetime(2010, 2, 1),  '19.99'),
                (datetime(2010, 3, 1),  '19.99'),
                (datetime(2010, 4, 1),  '19.99'),
                (datetime(2010, 5, 1),  '19.99'),
                (datetime(2010, 6, 1),  '19.99'),
                (datetime(2010, 7, 1),  '19.99'),
                (datetime(2010, 8, 1),  '19.99'),
                (datetime(2010, 9, 1),  '19.99'),
                (datetime(2010, 10, 1), '19.99'),
            ))

    def test_plans_d(self):
        self._do_test(RentalPlan.PlanD, (
                (datetime(2010, 1, 1),  '59.99'),
            ))

    def test_plans_e(self):
        self._do_test(RentalPlan.PlanE, (
                (datetime(2010, 1, 1), '119.99'),
            ))

    def test_expirations(self):
        self.assertEqual(RentalPlan.get_expiration_date(RentalPlan.PlanA, datetime(2010, 1, 1)), None)
        self.assertEqual(RentalPlan.get_expiration_date(RentalPlan.PlanB, datetime(2010, 1, 1)), None)
        self.assertEqual(RentalPlan.get_expiration_date(RentalPlan.PlanC, datetime(2010, 1, 1)), None)
        self.assertEqual(RentalPlan.get_expiration_date(RentalPlan.PlanD, datetime(2010, 1, 1)), datetime(2010, 5, 1))
        self.assertEqual(RentalPlan.get_expiration_date(RentalPlan.PlanE, datetime(2010, 1, 1)), datetime(2010, 8, 1))

    def test_bonus(self):
        self.assertEqual(RentalPlan.get_bonus(RentalPlan.PlanA), Decimal('0.0'))
        self.assertEqual(RentalPlan.get_bonus(RentalPlan.PlanB), Decimal('0.0'))
        self.assertEqual(RentalPlan.get_bonus(RentalPlan.PlanC), Decimal('0.0'))
        self.assertEqual(RentalPlan.get_bonus(RentalPlan.PlanD), Decimal('10.0'))
        self.assertEqual(RentalPlan.get_bonus(RentalPlan.PlanE), Decimal('15.0'))

if __name__ == '__main__':
    main()
