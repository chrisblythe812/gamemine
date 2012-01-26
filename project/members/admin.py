from logging import debug #@UnusedImport

from django.db.models import Sum, Avg
from django.contrib import admin
from django.http import Http404

from models import Profile
from project.buy_orders.models import BuyCart
from project.trade.models import TradeListItem

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'shipping_address', 'card_number', 'billing_address', 'account_status']
    list_filter = ['account_status', 'shipping_state']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email']
    list_editable = []
    fieldsets = (
        (None, {
            'fields': ('account_status', 'store_credits', 'strikes',),
        }),
        (None, {
            'fields' : ('phone', 'affiliate'),
        }),
        ('Shipping Address', {
            'fields': ('shipping_address1', 'shipping_address2', 'shipping_city', 'shipping_state', 'shipping_zip',),
        }),
    )

    class Media:
        css = {
            "all": ("css/admin/admin.css",)
        }

    def change_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, admin.util.unquote(object_id))
        if obj is None:
            raise Http404('Profile object with primary key %d does not exist.' % object_id)

        last_order_buy = obj.user.buyorder_set.order_by('-id')
        last_order_buy = last_order_buy[0] if len(last_order_buy) > 0 else None

        last_order_trade = obj.user.tradeorder_set.order_by('-id')
        last_order_trade = last_order_trade[0] if len(last_order_trade) > 0 else None

        last_order_rent = obj.user.rentorder_set.order_by('-id')
        last_order_rent = last_order_rent[0] if len(last_order_rent) > 0 else None

        stat = {
            'buy': {
                'last_date': last_order_buy.create_date if last_order_buy else '',
                'status': 'Active' if obj.user.buyorder_set.count() else 'Inactive',
                'earned_total': obj.user.buyorder_set.aggregate(Sum('total'))['total__sum'] or 0,
                'earned_avg': obj.user.buyorder_set.aggregate(Avg('total'))['total__avg'] or 0,
            },
            'trade': {
                'last_date': last_order_trade.create_date if last_order_trade else '',
                'status': 'Active' if obj.user.tradeorder_set.count() else 'Inactive',
                'earned_total': obj.user.tradeorder_set.aggregate(Sum('total'))['total__sum'] or 0,
                'earned_avg': obj.user.tradeorder_set.aggregate(Avg('total'))['total__avg'] or 0,
            },
            'rent': {
                'last_date': last_order_rent.date_rent if last_order_rent else '',
                'status': 'Active' if obj.user.rentorder_set.count() else 'Inactive',
                'earned_total': obj.user.billinghistory_set.filter(status=0).aggregate(Sum('debit'))['debit__sum'] or 0,
                'earned_avg': obj.user.billinghistory_set.filter(status=0).aggregate(Avg('debit'))['debit__avg'] or 0,
            },
        }
        stat['earned_total'] = (stat['buy']['earned_total'] + stat['trade']['earned_total'] + stat['rent']['earned_total']) / 3
        stat['earned_avg'] = (stat['buy']['earned_avg'] + stat['trade']['earned_avg'] + stat['rent']['earned_avg']) / 3

        last_order = {}
        last_order['buy'] = last_order_buy
        last_order['trade'] = last_order_trade
        last_order['rent'] = last_order_rent

        buy_cart, _created = BuyCart.objects.get_or_create(user=obj.user)
        trade_list = TradeListItem.get_for_user(obj.user)

        extra_context = extra_context or {}
        extra_context.update({
            'stat': stat,
            'last_order': last_order,
            'cart': buy_cart,
            'cart_total': sum([item.get_retail_price() * item.quantity for item in buy_cart.items.all()]),
            'trade_list': trade_list,
            'trade_total': sum([item.get_price() for item in trade_list]),
            })
        return super(ProfileAdmin, self).change_view(request, object_id, extra_context)

    def _format_address(self, data, prefix=None):
        k = ['address1', 'address2', 'city', 'state', 'zip_code']
        v = []
        for key in k:
            if prefix:
                key = '_'.join((prefix, key))
            if key in data and data[key]:
                v.append(data[key])
        return ', '.join(v)

    def full_name(self, obj):
        return ' '.join([obj.user.first_name, obj.user.last_name])

    def shipping_address(self, obj):
        return self._format_address(obj.get_shipping_address_data())

    def billing_address(self, obj):
        return self._format_address(obj.get_billing_address_data())

    def email(self, obj):
        return obj.user.email

    def card_number(self, obj):
        return obj.get_billing_card_display()

admin.site.register(Profile, ProfileAdmin)

