from decimal import Decimal

from project.taxes.models import Tax


def get_tax_amount(amount, state, county=None):
    tax = Tax.get_value(state, county)
    return Decimal('%.2f' % (amount * tax / Decimal('100.0')))
