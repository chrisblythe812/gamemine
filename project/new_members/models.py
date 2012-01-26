from uuid import uuid4

from project.members.models import Profile as OldProfile, BillingCard
from project.new_rent.models import MemberRentalPlan, RentalPlanStatus


class Profile(OldProfile):
    @property
    def billing_card(self):
        return BillingCard.objects.get(user=self.user)

    @property
    def email(self):
        return self.user.email

    @property
    def member_rental_plan(self):
        try:
            return MemberRentalPlan.objects.get(status=RentalPlanStatus.Active, user=self.user)
        except MemberRentalPlan.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        # Processing shipping data
        self.calc_shipping_checksum(False)
        self.link_to_dropship(dropship=None, save=False)
        if "request" in kwargs or getattr(self, "request", None):
            request = kwargs.get("request") or getattr(self, "request")
            self.campaign_cid = str(request.campaign_id)
            self.sid = str(request.sid)
            self.affiliate = str(request.affiliate)

        return super(Profile, self).save(*args, **kwargs)

    class Meta:
        proxy = True
