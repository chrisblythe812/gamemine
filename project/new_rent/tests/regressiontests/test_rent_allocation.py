from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth.models import User

from project.catalog.models.items import Item
from project.new_rent.models import RentalPlan
from project.new_rent.tests.regressiontests.add_item import AddItemTestCase
from project.new_rent.tests.regressiontests.signup import SignUpTestCase
from project.rent.models import RentOrder, RentOrderStatus
from project.new_members.models import Profile
from project.inventory.models import InventoryStatus


class RentAllocationTests(TestCase, AddItemTestCase, SignUpTestCase):
    def test_rent_allocation(self):
        item = Item.objects.all()[0]
        inventory = item.inventory_set.filter(status=InventoryStatus.InStock)[0]
        # New Monthly 1 Game Plan
        self.signup_plan(RentalPlan.objects.get(slug="unlimited1"))
        self.add_item_to_rentlist(item)

        self.assertEqual(RentOrder.objects.count(), 0)
        call_command("rent", "process_matrix")
        self.assertEqual(RentOrder.objects.filter(status=RentOrderStatus.Pending).count(), 1)
        self.assertTrue(RentOrder.objects.all()[0].shipping_state)

        self.client.logout()
        user = User.objects.create(
            username="test_admin",
            email="admin@email.com",
            is_staff=True,
            is_superuser=True)
        user.set_password("123")
        user.save()
        Profile.objects.create(user=user, group=100)
        self.client.login(username="test_admin", password="123")

        self.client.post(
            reverse("staff:page", kwargs={"path": "Rent/Orders"}),
            data={"barcode": inventory.barcode})
        self.assertEqual(RentOrder.objects.filter(status=RentOrderStatus.Prepared).count(), 1)

        ids = ",".join([str(pk) for pk in RentOrder.objects.values_list("pk", flat=True)])
        self.client.get(reverse("staff:rent_mark_shipped") + "?ids=%s" % ids)
        self.assertEqual(RentOrder.objects.filter(status=RentOrderStatus.Shipped).count(), 1)
