from django.test import TestCase
from project.new_members.forms import ProfileAndShippingCreationForm


class FormTests(TestCase):
    def setUp(self):
        self.data = {
            "username": "test_user",
            "email": "test@email.com",
            "password": "123456",
            "confirm_password": "123456",
            "how_did_you_hear": "1",
            "phone_number": "(123) 123-1234",

            "first_name": "John",
            "last_name": "Brown",
            "address1": "13 Test St",
            "address2": "app. 13",
            "city": "Test City",
            "zip_code": "12345",
            "state": "CA",
        }

    def test_profile_shipping_form(self):
        del self.data["how_did_you_hear"]
        psh_form = ProfileAndShippingCreationForm(self.data)
        self.assertEqual(psh_form.errors, {'how_did_you_hear': [u'Please tell how did you hear about us.']})

        self.data.update({"how_did_you_hear": "1"})
        psh_form = ProfileAndShippingCreationForm(self.data)
        self.assertTrue(psh_form.is_valid())
        psh_form.save(commit=False)

    def test_profile_shipping_form2(self):
        _data = {}
        for key, value in self.data.items():
            _data["0-%s" % key] = value
        psh_form = ProfileAndShippingCreationForm(_data, prefix="0")
        self.assertTrue(psh_form.is_valid())
