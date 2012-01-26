from project.new_rent.models import RentalPlan


def common(request):
    if request.user.is_authenticated() and request.user.get_profile().member_rental_plan:
        current_member_rental_plan = request.user.get_profile().member_rental_plan
        current_rental_plan = current_member_rental_plan.rental_plan
    else:
        current_rental_plan = None
        current_member_rental_plan = None

    return {
        'current_member_rental_plan': current_member_rental_plan,
        'current_rental_plan': current_rental_plan,
        'minimal_rent_charge': RentalPlan.objects.get(slug="unlimited1").first_payment_amount,
    }
