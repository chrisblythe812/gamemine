from django_snippets.auth.forms import AuthenticationByEmailForm
from project.members.forms import SignupForm 
from project.rent.models import RentList
from project.trade.models import TradeListItem

def core(request):
    result = {}

    if not request.user.is_authenticated():
        result['login_form'] = AuthenticationByEmailForm.create(request)
        result['sigup_form'] = SignupForm(request)

    lists_size = request.buy_list.count() + \
        RentList.get(request=request).count() + \
        TradeListItem.get(request).count()

    result['lists_size'] = lists_size

    return result

