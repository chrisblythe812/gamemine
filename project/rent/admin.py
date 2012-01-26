from django.contrib import admin
from django.contrib.auth import decorators

from django_snippets.views import simple_view

from models import RentList, MemberRentalPlan, RentalPlan, RentOrder
from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse


class RentOrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'full_name', 'item', 'upc', 'platform', 'status', 'date_rent', 'date_shipped', 'date_returned', 'source_dc', 'home_dc']
    list_filter = ['status', 'source_dc', 'date_rent', 'date_shipped', 'date_returned',]
    search_fields = ['date_rent', 'date_shipped', 'date_returned']
    raw_id_fields = ['inventory', 'item']
    fieldsets = (
        (None, {
            'fields': ('status', 'date_shipped', ),
        }),
    )

    def upc(self, obj):
        return obj.item.upc
#
    def full_name(self, obj):
        return ' '.join([obj.user.first_name, obj.user.last_name])

    def platform(self, obj):
        return obj.item.category

    def home_dc(self, obj):
        return obj.user.get_profile().dropship


class MemberRentalPlanAdmin(admin.ModelAdmin):
    list_filter = ['status', 'plan']
    list_display = ['id','plan', 'full_name', 'status', 'status_message', 'start_date', 'expiration_date', 'next_payment_date', 'next_payment_amount', 'delinquent_next_check', 'fails', 'card_expired']
    search_fields = ['user__username', 'user__email', 'user__id']

    def full_name(self, obj):
        return ' '.join([obj.user.first_name, obj.user.last_name])

    def fails(self, obj):
        return obj.payment_fails_count


class RentalPlanAdmin(admin.ModelAdmin):
    list_display = ['description', 'first_month', 'thereafter_months', 'months', 'expire_in', 'store_credits', 'games_allowed']


admin.site.register(RentOrder, RentOrderAdmin)
admin.site.register(MemberRentalPlan, MemberRentalPlanAdmin)
admin.site.register(RentalPlan, RentalPlanAdmin)


@decorators.user_passes_test(lambda u: u.is_superuser)
@simple_view('rent/admin/pick_list.html')
def pick_list(request):
    return {
        'title': 'Rent pick list',
        'pending_list': RentList.pending_list(),
    }


@decorators.user_passes_test(lambda u: u.is_superuser)
def create_order(request, id):
    o = get_object_or_404(RentList, pk=id)
    order = o.create_order()
    return redirect(reverse('admin:rent_rentorder_change', args=[order.id]))


#@decorators.user_passes_test(lambda u: u.is_superuser)
#@simple_view('rent/admin/view_order.html')
#def view_order(request, id):
#    o = get_object_or_404(RentOrder, pk=id)


@decorators.user_passes_test(lambda u: u.is_superuser)
def generate_order_labels(request, id):
    o = get_object_or_404(RentOrder, pk=id)
    o.request_outgoing_mail_label()
    o.request_incoming_mail_label()
    o.save()
    return redirect(reverse('admin:rent_rentorder_change', args=[o.id]))
