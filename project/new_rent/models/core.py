"""
``RentalPlan`` is new implementation of model,
wrapper around ``rent.models.BaseRentalPlan``.

Some attributes of ``RentalPlan`` are hardcoded.

``MemberRentalPlan`` is new implementation of model,
wrapper around ``rent.models.BaseMemberRentalPlan``.


How Free Trial Currently Works
==============================

When creating ``MemberRentalPlan`` we are setting ``scheduled_plan`` to
``RentalPlan.Plan`` and ``next_payment_type`` to "AUTH_ONLY", ``next_period_date`` to +10d.
When first billing occurs we are authorizing $19.99 from user's CC ("AUTH_ONLY" request).
In 10 days ``recurring_billing`` proccess occurs and which calls ``activate_scheduled_plan`` method
which removes user's current ``MemberRentalPlan`` and creates new one with ``next_payment_type``
set to "PRIOR_AUTH_CAPTURE".
Next time ``recurring_billing`` proccess occurs it captures money from user's CC
("PRIOR_AUTH_CAPTURE" request) and sets ``next_payment_type`` to "AUTH_CAPTURE".
"""
import datetime

from django.db.models.signals import pre_delete
from django.utils.translation import ungettext as _

from django_snippets.utils.datetime import inc_date
from project.rent.models import (
    BaseRentalPlan, BaseMemberRentalPlan,
    MemberRentalPlan as OldMemberRentalPlan, MemberRentalPlanHistory)
from project.new_rent.models.member_rental_plan.billing import MemberRentalPlanBillingMixin
from project.new_rent.models.member_rental_plan.notifications import \
    MemberRentalPlanNotificationsMixin
from project.new_rent.models.rental_plan.billing import RentalPlanBillingMixin
from project.new_rent.models.rental_plan.managers import RentalPlanManager

__all__ = ["RentalPlanManager", "RentalPlan", "MemberRentalPlan"]


class RentalPlan(BaseRentalPlan, RentalPlanBillingMixin):
    class Meta:
        proxy = True
        ordering = ["games_allowed"]

    active_plans = [
        BaseRentalPlan.PlanF,  # 1 Game Plan
        BaseRentalPlan.PlanG,  # 2 Game Plan
        BaseRentalPlan.PlanH,  # 2 Game Plan Free Trial
        19  # 3 Game Plan
    ]

    objects = RentalPlanManager()

    @property
    def first_payment_amount(self):
        return self.first_month

    @property
    def thereafter_payments_amount(self):
        return self.thereafter_months

    @property
    def pay_every(self):
        return self._payment_matrix[self.plan][2]

    @property
    def period_in_months(self):
        return self.months

    @property
    def description2(self):
        return _(
            "%s Game out-at-a-time",
            "%s Games out-at-a-time",
            self.games_allowed
        ) % self.games_allowed

    @property
    def description3(self):
        unlimited = "Unlimited" if self.is_unlimited else "Limited"
        return "%s (%s)" % (self.description2, unlimited)

    def __unicode__(self):
        return self.description

    def get_expiration_date(self, plan_start_date=None, downgrade=False):
        _plan = self._payment_matrix[self.pk]
        exp = _plan[3]
        if not exp:
            return None
        if downgrade:
            exp -= 1
        if plan_start_date is None:
            plan_start_date = datetime.date.today()
        return inc_date(plan_start_date, exp)

    def is_prepaid(self):
        return bool(self.expire_in)

    def months_prepaid(self):
        if self.is_prepaid:
            return self.expire_in - 1
        return None

    def is_unlimited(self):
        return not bool(self.out_per_month)

    def is_upgrade(self, new_plan):
        """
        Returns ``True`` if new plan is an upgrade from current plan,
        otherwise ``False``
        """
        assert self != new_plan, "Current instance and new_plan should be different"
        if new_plan.is_prepaid:
            return new_plan.games_allowed > self.games_allowed
        return new_plan.thereafter_payments_amount > self.thereafter_payments_amount


class MemberRentalPlan(BaseMemberRentalPlan, MemberRentalPlanBillingMixin,
                       MemberRentalPlanNotificationsMixin):
    class Meta:
        proxy = True

    def get_rental_plan(self):
        return RentalPlan.objects.get(pk=self.plan)

    def set_rental_plan(self, value):
        self.plan = value.pk

    rental_plan = property(get_rental_plan, set_rental_plan)

    def get_scheduled_rental_plan(self):
        try:
            return RentalPlan.objects.get(pk=self.scheduled_plan)
        except RentalPlan.DoesNotExist:
            return None

    def set_scheduled_rental_plan(self, value):
        self.scheduled_plan = value.pk

    scheduled_rental_plan = property(get_scheduled_rental_plan, set_scheduled_rental_plan)

    def activate_scheduled_plan(self):
        res = OldMemberRentalPlan.__dict__["activate_scheduled_plan"](
            self
        )
        if RentalPlan.objects.get(pk=self.plan).slug == "free_trial":
            res.next_payment_type = "PRIOR_AUTH_CAPTURE"
            res.save()
        return res

    def set_status(self, status, message="", save=True):
        return OldMemberRentalPlan.__dict__["set_status"](
            self, status, message, save
        )

    def __unicode__(self):
        return OldMemberRentalPlan.__dict__["__unicode__"](self)


def member_rental_plan_pre_delete(sender, instance, **kwargs):
    MemberRentalPlanHistory.create(instance)
pre_delete.connect(member_rental_plan_pre_delete, MemberRentalPlan)
