
# TODO(Roman):
# ``available_for_change`` and ``available_for_signup`` should be
# somewhere in ``project.new_members``.

from django.db import models

from project.tds.utils import is_eligible_for_free_trial


class RentalPlanManager(models.Manager):
    def all_active(self):
        from project.new_rent.models import RentalPlan

        return self.filter(pk__in=RentalPlan.active_plans)

    def all_deprecated(self):
        from project.new_rent.models import RentalPlan

        return self.exclude(pk__in=RentalPlan.deprecated_plans)

    def available_for_signup(self, request):
        plans = self.filter(slug__in=["unlimited1", "unlimited2"])

        if (
            # Disable free trial for registered users
            not request.user.is_authenticated() and
            is_eligible_for_free_trial(request)
            ):
            plans |= self.filter(slug="free_trial")
        return plans

    def available_for_change(self, request):
        from project.members.models import BillingHistory, TransactionStatus
        from project.members.utils import get_user_current_rental_plan

        plans = self.all_active()

        current_plan = get_user_current_rental_plan(request)
        plans = plans.exclude(pk=current_plan.pk)

        # No plan change available for free trial
        if current_plan.slug == "free_trial":
            return self.none()

        # Remove Free Trial
        plans = plans.exclude(slug="free_trial")

        # Removing duplicated plans (old vs new)
        _ = {
            "old_unlimited": "unlimited2",
        }
        _plan_to_remove = _.get(current_plan.slug)
        if _plan_to_remove:
            plans = plans.exclude(slug=_plan_to_remove)

        # All prepaid plans are 2 GAMEs out-at-a-time,
        # so removing 2 GAMEs out-at-a-time monthly
        if current_plan.is_prepaid():
            plans = plans.exclude(slug__in=["unlimited1", "unlimited2"])

        # Checking if user has more than 2 successful billings
        allow_3_game_plan = BillingHistory.objects.filter(
            status=TransactionStatus.Passed, user=request.user).count() > 2

        if not allow_3_game_plan:
            plans = plans.exclude(slug="unlimited3")

        return plans

    def available_for_change_limited(self, request):
        plans = self.available_for_change(request).exclude(out_per_month=None)
        return plans

    def available_for_change_unlimited(self, request):
        plans = self.available_for_change(request).filter(out_per_month=None)
        return plans
