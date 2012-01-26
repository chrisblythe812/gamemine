from project.rent.models import MemberRentalPlan as OldMemberRentalPlan


class MemberRentalPlanNotificationsMixin(object):
    def send_plan_subscription_successfull_email(self):
        return OldMemberRentalPlan.__dict__["send_plan_subscription_successfull_email"](
            self
        )

    def send_billing_charge_approved(self, cc_type, cc_num, amount):
        return OldMemberRentalPlan.__dict__["send_billing_charge_approved"](
            self, cc_type, cc_num, amount
        )

    def send_recurring_billing_charge_declined(self, attempt):
        return OldMemberRentalPlan.__dict__["send_recurring_billing_charge_declined"](
            self, attempt
        )
