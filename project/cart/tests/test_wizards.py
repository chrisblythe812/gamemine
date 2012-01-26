from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User

from project.cart.wizards import *
from project.members.models import Profile, BillingCard
from project.catalog.models import Item
from project.buy_orders.models import BuyOrder, BuyOrderStatus

from project.inventory.models import DistributorItem,Distributor

from decimal import Decimal

import json
import urllib2


class TestWizards(TestCase):
    fixtures = ['categories','genres','publishers','types','test_item','dropships']
    def setUp(self):
        u = User(username='john',
                 email='john@wow.com',
                 is_active=True)
        u.set_password('johnpassword')
        u.save()
        p = Profile(user=u,
                       campaign_cid='0',
                       sid='0',
                       affiliate='0',
                       phone='(555) 555-5555',
                       shipping_address1="9518 New Waterford Cv",
                       shipping_zip="33446-9747",
                       shipping_state="FL",
                       shipping_city="Delray Beach",
                       shipping_county="Palm Beach",
                       shipping_checksum="0d35b4ffcb260482947680f48ba8e482",
                       )
        p.save()

        billing_card = BillingCard(user=u,
                type="visa",
                display_number="XXXX-XXXX-XXXX-1150",
                data = "XnSDaVgvyOUaZmrftFo0rKPFhyHdf+E6WyMxz45cG6yk4kr6ob0A+6mxnY8Xrf2IMXBEIBrNN7FhvyzpGb77JX0PG1sl8rDKhdPNMsa8xBt9pzVee9nsUXm3GYo2VRLpGLPrRoBphEPkdnGw",
                first_name="Mvi",
                last_name="Mvi",
                address1="9518 New Waterford Cv",
                address2="",
                city="Delray Beach",
                state="FL",
                county="Palm Beach",
                zip="33446-9747",
                checksum="670bee769cd1e3644e411110a6b32dd4",
                address_checksum="3e3c98e96e4dd335c59629b323892b5a"
        )
        billing_card.save()
        self.user = u
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


    def test_checkout(self):
        c = Client()
        c.login(username='john',password='johnpassword')
        response = c.get('/Cart/Add/100000077/',HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = c.post('/Cart/Add/100000077/',dict(condition='new',submit='cart'),HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = c.get('/Cart/Checkout/',HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        #response = c.post('/Cart/Checkout/',{
        #    "0-first_name":"Mvi",
        #    "0-last_name":"Mvi",
        #    "0-address1":"9518 New Waterford Cv",
        #    "0-address2":"",
        #    "0-city":"Delray Beach",
        #    "0-state":"FL",
        #    "0-zip_code":"33446-9747",
        #    "wizard_step":"0"
        #},HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        import fudge
        @fudge.patch('urllib2.urlopen','random.choice')
        def test(fake_urlopen,fake_choice):
            #faking an error in urllib2
            fake_urlopen.is_callable().raises(Exception("error"))
            #faking a choice that is made at the authorizenet api when in test mode to accept the order
            fake_choice.is_callable().returns(False)
            response = c.post('/Cart/Checkout/',{
                "1-first_name":"Mvi",
                "1-last_name":"Mvi",
                "1-address1":"9518 New Waterford Cv",
                "1-address2":"",
                "1-city":"Delray Beach",
                "1-state":"FL",
                "1-zip_code":"33446-9747",
                "1-type":"visa",
                "1-number":"4111111111111150",
                "1-exp_month":"3",
                "1-exp_year":"2011",
                "1-code":"123",
                "0-first_name":"Mvi",
                "0-last_name":"Mvi",
                "0-address1":"9518 New Waterford Cv",
                "0-address2":"",
                "0-city":"Delray Beach",
                "0-state":"FL",
                "0-zip_code":"33446-9747",
                "hash_0":"3081159020514cc7dbe50aa208897880877ef7d9",
                "wizard_step":"1"
            },HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            return response

        test_reponse = test()
        #now, making sure there are no ghost buyorder
        buy_orders = BuyOrder.objects.filter(user=self.user).exclude(status=BuyOrderStatus.Checkout).count()
        #import pdb;pdb.set_trace()
        self.assertEqual(buy_orders,0)

    def test_store_credit_checkout(self):
        c = Client()
        c.login(username='john',password='johnpassword')
        p = self.user.get_profile()
        p.store_credits = Decimal("18.99")
        p.locked_store_credits = Decimal("10.00")
        p.save()

        response = c.get('/Cart/Add/100000077/',HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = c.post('/Cart/Add/100000077/',dict(condition='new',submit='cart'),HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = c.get('/Cart/')
        import re
        p = re.compile(r"store_credits: parseFloat\('(?P<credit>[0-9\.]+)'\)")
        match = p.search(response.content)
        store_credits_shown = match.groupdict()['credit']
        response = c.post('/Cart/Apply-Credits/', dict(amount=store_credits_shown), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = c.get('/Cart/Checkout/',HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        #response = c.post('/Cart/Checkout/',{
        #    "0-first_name":"Mvi",
        #    "0-last_name":"Mvi",
        #    "0-address1":"9518 New Waterford Cv",
        #    "0-address2":"",
        #    "0-city":"Delray Beach",
        #    "0-state":"FL",
        #    "0-zip_code":"33446-9747",
        #    "wizard_step":"0"
        #},HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = c.post('/Cart/Checkout/',{
            "1-first_name":"Mvi",
            "1-last_name":"Mvi",
            "1-address1":"9518 New Waterford Cv",
            "1-address2":"",
            "1-city":"Delray Beach",
            "1-state":"FL",
            "1-zip_code":"33446-9747",
            "1-type":"visa",
            "1-number":"4111111111111150",
            "1-exp_month":"3",
            "1-exp_year":"2011",
            "1-code":"123",
            "0-first_name":"Mvi",
            "0-last_name":"Mvi",
            "0-address1":"9518 New Waterford Cv",
            "0-address2":"",
            "0-city":"Delray Beach",
            "0-state":"FL",
            "0-zip_code":"33446-9747",
            "hash_0":"3081159020514cc7dbe50aa208897880877ef7d9",
            "wizard_step":"1"
        },HTTP_X_REQUESTED_WITH='XMLHttpRequest')


        #now, making sure there are no ghost buyorder
        buy_orders = BuyOrder.objects.filter(user=self.user).exclude(status=BuyOrderStatus.Checkout).count()
        #import pdb;pdb.set_trace()
        self.assertEqual(buy_orders,0)
