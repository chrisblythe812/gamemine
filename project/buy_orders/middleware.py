from project.buy_orders.models import BuyList


class LazyBuyList(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_buy_list'):
            request._cached_buy_list = BuyList.get(request=request)
        return request._cached_buy_list


class BuyListMiddleware(object):
    def process_request(self, request):
        request.__class__.buy_list = LazyBuyList()
