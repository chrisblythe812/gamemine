from django.core.management.base import NoArgsCommand
from project.buy_orders.models import BuyOrder, BuyOrderStatus
from project.members.models import TransactionStatus, BillingCard


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        for o in BuyOrder.objects.filter(payment_transaction__status__in=[TransactionStatus.Passed, TransactionStatus.Authorized]).exclude(status=BuyOrderStatus.Checkout):
            print o.id
            o.status = BuyOrderStatus.Checkout
            o.first_name = o.user.first_name
            o.last_name = o.user.last_name

            o.shipping_address1 = o.user.profile.shipping_address1
            o.shipping_address2 = o.user.profile.shipping_address2
            o.shipping_city = o.user.profile.shipping_city
            o.shipping_state = o.user.profile.shipping_state
            o.shipping_county = o.user.profile.shipping_county
            o.shipping_zip_code = o.user.profile.shipping_zip
            
            cc = BillingCard.get(o.user)
            o.billing_first_name = cc.first_name
            o.billing_last_name = cc.last_name
            
            o.billing_address1 = cc.address1
            o.billing_address2 = cc.address2
            o.billing_city = cc.city
            o.billing_state = cc.state
            o.billing_county = cc.county
            o.billing_zip_code = cc.zip
            
            o.save()
            o.complete(True)
