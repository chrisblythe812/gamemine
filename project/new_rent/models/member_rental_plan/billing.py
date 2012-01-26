import datetime

from project.rent.models import (
    RentalPlanStatus,
    MemberRentalPlan as OldMemberRentalPlan)

from project.members.models import BillingCard


class MemberRentalPlanBillingMixin(object):
    def get_payment_description(self, new_or_reccuring, trans_id, reccuring=False):
        return OldMemberRentalPlan.__dict__["get_payment_description"](
            self, new_or_reccuring, trans_id, reccuring
        )

    def take_money(self, amount, tax, invoice_num, description, card=None,
                   shipping_data=None, billing_data=None, aim=None,
                   aim_data={}, profile=None, aim_method="capture"):
        return OldMemberRentalPlan.__dict__["take_money"](
            self, amount, tax, invoice_num, description, card,
            shipping_data, billing_data, aim, aim_data, profile,
            aim_method
        )

    def take_recurring_billing(self, aim_method="capture"):
        from project.new_rent.models import RentalPlan

        if self.next_payment_type == "AUTH_ONLY":
            aim_method = "authorize"
        elif self.next_payment_type == "PRIOR_AUTH_CAPTURE":
            success, res = self.get_last_payment().capture()
            if not success:
                if (res.aim_response.get("response_code") == 3 and
                    res.aim_response.get("response_reason_code") in [6, 7, 8]):
                    self.card_expired = True
                    msg = 'Credit card is expired'
                elif res.aim_response.get("response_reason_code") in [2, 3, 4]:
                    msg = 'Insufficient funds are available for this transaction.'
                elif res.aim_response.get("avs_response") == 'U':
                    msg = 'We do not accept prepaid cards.'
                else:
                    msg = 'We are unable to process you credit card at this time.'

                self.set_status(RentalPlanStatus.Delinquent, msg)
                self.send_recurring_billing_charge_declined(1)
                return False
            (self.next_payment_date,
             self.next_payment_amount,
             _) = RentalPlan.objects.get(pk=self.plan).get_next_payment(datetime.date.today())
            self.next_payment_type = "AUTH_CAPTURE"
            self.save()

            billing_card = BillingCard.get(self.user)

            if res.debit > 0:
                self.send_billing_charge_approved(
                    billing_card.get_type_display(),
                    billing_card.display_number,
                    res.debit)

            self.user.get_profile().clear_locked_store_credits()
            self.set_status(RentalPlanStatus.Active)

            return True

        return OldMemberRentalPlan.__dict__["take_recurring_billing"](
            self, aim_method)

    def _create_aim_data(self, aim_data, card, shipping_data, billing_data, invoice_num,
                         description, user, profile=None):
        return OldMemberRentalPlan.__dict__["_create_aim_data"](
            self, aim_data, card, shipping_data, billing_data, invoice_num,
            description, user, profile
        )

    def get_last_payment(self):
        return OldMemberRentalPlan.__dict__["get_last_payment"](self)
