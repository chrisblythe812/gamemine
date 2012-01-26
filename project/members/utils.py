def get_card_display_number(number):
    last_digits = number[-4:]
    display_number = "XXXX-XXXX-XXXX-%s" % last_digits
    return display_number


def build_aim_data(shipping_data, billing_data, billing_card_data,
                   invoice_num, description, email=None, customer_ip=None,
                   tax=None):
    exp = "%s/%s" % (billing_card_data.pop("exp_month"), billing_card_data.pop("exp_year")[-2:])
    del billing_card_data["type"]
    aim_data = {}
    aim_data["billing"] = billing_data
    aim_data["shipping"] = shipping_data
    aim_data["invoice_num"] = invoice_num
    aim_data["description"] = description
    aim_data.update(billing_card_data)
    aim_data["exp"] = exp
    if email is not None:
        aim_data["x_email"] = email
    if customer_ip is not None:
        aim_data["x_customer_ip"] = customer_ip
    if aim_data is not None:
        aim_data["x_tax"] = tax
    return aim_data


def get_user_current_rental_plan(request):
    from project.new_rent.models import RentalPlan, MemberRentalPlan

    mrp = MemberRentalPlan.objects.get(user=request.user)
    return RentalPlan.objects.get(pk=mrp.plan)
