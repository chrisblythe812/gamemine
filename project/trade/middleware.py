from datetime import datetime
from project.trade.models import TradeCart


class LazyCart(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_trade_cart'):
            request._cached_trade_cart = TradeCart.get(request)
        return request._cached_cart


class CartMiddleware(object):
    def process_request(self, request):
        request.__class__.trade_cart = LazyCart()
        request.trade_cart.last_session_timestamp = datetime.now()
        request.trade_cart.save()

