# -*- coding: utf-8 -*-
from models import MailingList
def extras(request):
    """
    Verifica se tem lista publica ou não
    """
    return {'os3_marketing_public_list':MailingList.objects.filter(type=MailingList.PUBLIC).count() > 0}
