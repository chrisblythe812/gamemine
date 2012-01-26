from decimal import Decimal
import json


from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core import mail
from nose.plugins.skip import SkipTest

from project.rent.models import RentalPlan, MemberRentalPlan, RentalPlanStatus
from project.catalog.models import Item
from project.inventory.models import DistributorItem, Distributor


class TestWizards(TestCase):
    fixtures = ['categories','genres','publishers','types','test_item','dropships','rental_plans']
    def setUp(self):
        raise SkipTest
        self.game_item = Item.objects.get(pk=100000077)
        #creating a distributor and an entry in stock for this game
        self.fake_distributor = Distributor(id=5,name='fake distributor', address='fake address',new_games_vendor=True)
        self.fake_distributor.save()
        self.game_distributor_item = DistributorItem(distributor=self.fake_distributor,
            item=self.game_item,
            is_new=True,
            retail_price=Decimal('18.99'),
            wholesale_price=Decimal('18.99'),
            quantity=50,
            profit=1,
            retail_price_used_vendor=Decimal('11.99'),
            wholesale_price_used=Decimal('11.99'),
            quantity_used=10,
            trade_price=Decimal('11.99'),
            trade_price_incomplete=Decimal('5.99')
        )
        self.game_distributor_item.save()


    def test_nonmember_rental_signup(self):
        import re
        c = Client()
        response = c.get('/Rent/Add/100000077/',HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = c.post('/Rent/Add/100000077/',HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        json_response = json.loads(response.content)
        wizard_url = json_response['goto_url']

        response = c.get(wizard_url,HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        form_data = {'0-plan':RentalPlan.PlanB}
        response = c.post(wizard_url,form_data.copy(),HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        json_response = json.loads(response.content)
        form_html = json_response['form']
        hash_0 = re.search(r'hash_0" value="(?P<hash_0>[^"]*)',form_html).groupdict()['hash_0']

        form_data['1-address1'] = '306 Broadway'
        form_data['1-address2'] = ''
        form_data['1-city'] = 'New York'
        form_data['1-confirm_password'] = 'mmmmmm'
        form_data['1-email'] = 'm@mm.com'
        form_data['1-first_name'] = 'Mauricio'
        form_data['1-how_did_you_hear'] = '1'
        form_data['1-last_name'] = 'Lima'
        form_data['1-password'] = 'mmmmmm'
        form_data['1-phone_number'] = '(555) 888-9999'
        form_data['1-state'] = 'NY'
        form_data['1-username'] = 'mmmmm'
        form_data['1-zip_code'] = '10007-1223'
        form_data['hash_0'] = hash_0
        form_data['wizard_step'] = '1'
        response = c.post(wizard_url,form_data.copy(),HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        json_response = json.loads(response.content)
        form_html = json_response['form']
        hash_1 = re.search(r'hash_1" value="(?P<hash_1>[^"]*)',form_html).groupdict()['hash_1']


        form_data['2-address1'] = '306 Broadway'
        form_data['2-address2'] = ''
        form_data['2-city'] = 'New York'
        form_data['2-code'] = '111'
        form_data['2-exp_month'] = '3'
        form_data['2-exp_year'] = '2013'
        form_data['2-first_name'] = 'Mauricio'
        form_data['2-last_name'] = 'Lima'
        form_data['2-number'] = '4111111111111114'
        form_data['2-state'] = 'NY'
        form_data['2-type'] = 'visa'
        form_data['2-zip_code'] = '10007-1223'
        form_data['hash_1'] = hash_1
        form_data['wizard_step'] = '2'

        response = c.post(wizard_url,form_data.copy(),HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        u = User.objects.get(username='mmmmm')
        user_rental_plan = MemberRentalPlan.objects.get(user=u)
        self.assertEqual(user_rental_plan.plan, RentalPlan.PlanB)
        self.assertEqual(user_rental_plan.status, RentalPlanStatus.Active)

        self.assertEqual(len(mail.outbox), 1)
