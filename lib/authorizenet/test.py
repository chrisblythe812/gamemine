from decimal import Decimal


# Dummy data
class DummyData:
    amount = Decimal("8.99")
    number = "4111111111111111"
    exp = "1/12"
    code = "123"
    billing = {
        "address1": u"1 Test St",
        "address2": u"",
        "city": u"Test City",
        "code": u"123",
        "country": "USA",
        "exp_month": u"1",
        "exp_year": u"2012",
        "first_name": u"Roman",
        "last_name": u"Dolgiy",
        "number": u"4111111111111111",
        "state": u"AZ",
        "type": u"visa",
        "zip_code": u"05105",
    }
    spipping = {
        "address1": u"1 Test St",
        "address2": u"",
        "city": u"Test City",
        "confirm_password": u"19891010",
        "country": "USA",
        "email": u"roman@bravetstudio.com",
        "first_name": u"Roman",
        "how_did_you_hear": u"2",
        "last_name": u"Dolgiy",
        "password": u"19891010",
        "state": u"AZ",
        "username": u"t0ster",
        "zip_code": u"05105",
    }
    invoice_num = "RENT_NEW_44596"
    description = "Monthly Membership - Aug 11, 2011 - Sep 11, 2011"
