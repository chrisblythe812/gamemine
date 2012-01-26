import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.core import mail
from django.conf import settings

from django_snippets.utils.datetime import inc_months
from project.members.models import Profile, BillingHistory
from project.rent.models import MemberRentalPlan, RentList, RentOrder, RentOrderStatus
from project.catalog.models import Item
from project.inventory.models import Dropship
from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.new_rent.models import RentalPlan


class RecurrentTestCase(TestCase, SignUpTestCase):
    fixtures = ['categories', 'distributors', 'genres', 'publishers', 'types',
                'ratings', 'games', 'tags', 'test_item', 'dropships']

    def setUp(self):
        pass

    def tearDown(self):
        settings.AUTH_NET_CONF["test_response_code"] = 1  # All OK

    def test_recurrent(self):
        # Member signed up for rental plan and have been billed first
        # time
        plan = RentalPlan.objects.get(slug="unlimited1")
        self.signup_plan(plan)
        mrp = MemberRentalPlan.objects.all()[0]

        # User adds item to rent list
        # rl = RentList.objects.create(user=mrp.user, item=Item.objects.all()[0])
        # dc = Dropship.objects.all()[0]
        # ro = RentOrder.create(mrp.user, rl, dc)
        # ro.status = RentOrderStatus.Shipped
        # ro.save()

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(BillingHistory.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Gamemine - Thanks for Joining Gamemine!")
        self.assertEqual(mrp.get_status_display(), "Active")

        # Calling ``rent recurring_billing`` command, member should
        # not be billed yet
        call_command("rent", "recurring_billing")
        self.assertEqual(BillingHistory.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        # Calling ``rent recurring_billing`` command, member should be
        # billed
        mrp.next_payment_date = datetime.date.today()
        mrp.save()
        call_command("rent", "recurring_billing")
        self.assertEqual(BillingHistory.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Gamemine - Billing Charge Approved")
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(mrp.next_payment_date, inc_months(datetime.date.today(), 1))

        # Calling ``rent recurring_billing`` command, member should
        # not be billed
        call_command("rent", "recurring_billing")
        self.assertEqual(BillingHistory.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

        # Trying to bill member with insufficient funds on CC
        # Declined Notification # 1
        settings.AUTH_NET_CONF["test_response_code"] = 2  # Insufficient funds
        mrp = MemberRentalPlan.objects.all()[0]
        mrp.next_payment_date = datetime.date.today()
        mrp.save()
        call_command("rent", "recurring_billing")
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(BillingHistory.objects.count(), 3)
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[2].subject, "Oops, we have a billing problem!")
        self.assertEqual(mrp.get_status_display(), "Delinquent")
        self.assertEqual(mrp.payment_fails_count, 1)
        self.assertEqual(mrp.delinquent_next_check, datetime.date.today() + datetime.timedelta(5))
        # ``next_payment_date`` remains the same
        self.assertEqual(mrp.next_payment_date, datetime.date.today())

        # ``recurring_billing`` command only porcesses ``Active``
        # ``MemberRentalPlans``
        call_command("rent", "recurring_billing")
        self.assertEqual(BillingHistory.objects.count(), 3)

        call_command("rent", "delinquent_billing")
        self.assertEqual(BillingHistory.objects.count(), 3)
        self.assertEqual(mrp.delinquent_next_check, datetime.date.today() + datetime.timedelta(5))

        # Declined Notification # 2
        MemberRentalPlan.objects.update(delinquent_next_check=datetime.date.today())
        call_command("rent", "delinquent_billing")
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(BillingHistory.objects.count(), 4)
        self.assertEqual(len(mail.outbox), 4)
        self.assertEqual(mail.outbox[3].subject, "Problem with your Recent Transaction!")
        self.assertEqual(mrp.get_status_display(), "Delinquent")
        self.assertEqual(mrp.payment_fails_count, 2)
        self.assertEqual(mrp.delinquent_next_check, datetime.date.today() + datetime.timedelta(5))

        # Declined Notification # 3
        MemberRentalPlan.objects.update(delinquent_next_check=datetime.date.today())
        call_command("rent", "delinquent_billing")
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(BillingHistory.objects.count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(mail.outbox[4].subject, "We Can't Send you Games!")
        self.assertEqual(mrp.get_status_display(), "Delinquent")
        self.assertEqual(mrp.payment_fails_count, 3)
        # 4th billing attempt and notification in 4 days (14 days from first fail)
        # fails
        # self.assertEqual(mrp.delinquent_next_check, datetime.date.today() + datetime.timedelta(4))

        # Declined Notification # 4
        MemberRentalPlan.objects.update(delinquent_next_check=datetime.date.today())
        call_command("rent", "delinquent_billing")
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(BillingHistory.objects.count(), 6)
        self.assertEqual(len(mail.outbox), 6)
        self.assertEqual(mail.outbox[5].subject, "Problem with your Recent Transaction!")
        self.assertEqual(mrp.get_status_display(), "Delinquent")
        self.assertEqual(mrp.payment_fails_count, 4)
        # 5th billing attempt and notification in 4 days (18 days from first fail)
        # fails
        # self.assertEqual(mrp.delinquent_next_check, datetime.date.today() + datetime.timedelta(4))

        # Declined Notification # 5
        MemberRentalPlan.objects.update(delinquent_next_check=datetime.date.today())
        call_command("rent", "delinquent_billing")
        mrp = MemberRentalPlan.objects.all()[0]
        self.assertEqual(BillingHistory.objects.count(), 7)
        self.assertEqual(len(mail.outbox), 7)
        self.assertEqual(mrp.payment_fails_count, 5)
        # fails
        # self.assertEqual(mail.outbox[6].subject, "Your Rent Account is about to be Cancelled!")
        # fails
        # self.assertEqual(mrp.get_status_display(), "Delinquent")
        # 6th billing attempt and notification in 2 days (20 days from first fail)
        # fails
        # self.assertEqual(mrp.delinquent_next_check, datetime.date.today() + datetime.timedelta(2))

        # fails
        # Declined Notification # 6
        # MemberRentalPlan.objects.update(delinquent_next_check=datetime.date.today())
        # call_command("rent", "delinquent_billing")
        # mrp = MemberRentalPlan.objects.all()[0]
        # self.assertEqual(BillingHistory.objects.count(), 8)
        # self.assertEqual(len(mail.outbox), 8)
        # self.assertEqual(mail.outbox[7].subject, "Gamemine account has been canceled - Please return games")
        # self.assertEqual(mrp.get_status_display(), "Auto Canceled")
        # self.assertEqual(mrp.delinquent_next_check, None)
