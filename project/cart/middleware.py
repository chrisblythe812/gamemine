from datetime import datetime
from project.buy_orders.models import BuyCart


class LazyCart(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_cart'):
            request._cached_cart = BuyCart.get(request)
        return request._cached_cart


class CartMiddleware(object):
    def process_request(self, request):
        request.__class__.cart = LazyCart()
        request.cart.last_session_timestamp = datetime.now()
        request.cart.save()
