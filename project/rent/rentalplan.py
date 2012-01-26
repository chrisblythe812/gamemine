from project.rent.models import RentalPlan


def get_details(plan, request=None):
    return {
        RentalPlan.PlanA: {
            "plan": plan,
            "title": "Limited Monthly 1 Game Plan",
            "slug": "limited",
            "allowed_games": 1,
            "out_per_month": 2,
            "amount_to_charge": RentalPlan.get_start_payment_amount(plan),
            "price": RentalPlan.get_prices(plan)[1],
            "price_first_month": RentalPlan.get_prices(plan)[0],
        },
        RentalPlan.PlanB: {
            "plan": plan,
            "title": "Unlimited Monthly 2 Game Plan",
            "slug": "unlimited",
            "allowed_games": 2,
            "out_per_month": None,
            "amount_to_charge": RentalPlan.get_start_payment_amount(plan),
            "price": RentalPlan.get_prices(plan)[1],
            "price_first_month": RentalPlan.get_prices(plan)[0],
        },
    }[plan]
