import sys
import logging
import decimal
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from django_snippets.models.blowfish_field import BlowfishField


class MuzeUpdate:
    Successful = 0
    Fail = 1
    Dry = 2
    DryFail = 2

MUZE_UPDATE_STATUSES = (
    (MuzeUpdate.Successful, 'Successful'),
    (MuzeUpdate.Fail, 'Fail'),
    (MuzeUpdate.Dry, 'Dry Run'),
    (MuzeUpdate.DryFail, 'Dry Run (Fail)'),
)


class MuzeUpdateLog(models.Model):
    class Meta:
        ordering = ['-timestamp']

    timestamp = models.DateTimeField(default=datetime.now, db_index=True)
    status = models.IntegerField(choices=MUZE_UPDATE_STATUSES)
    message = models.TextField()
    checksum = models.CharField(max_length=64, db_index=True)
    filename = models.CharField(max_length=512)


def hide_data(k, v):
    if k == 'x_card_num':
        return '*' * len(v[:-4]) + v[-4:]
    if k == 'x_login':
        return '*************'
    return v


class AimRequest(models.Model):
    type = models.CharField(max_length=32, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    transaction_id = models.CharField(max_length=32, null=True)
    data = BlowfishField(key=settings.BILLING_CARDS_CRYPTO_KEY, null=True)

    def list_data(self):
        try:
            keys = self.data.keys()
            keys.sort()
            for k in keys:
                yield k[2:].replace('_', ' '), hide_data(k, self.data[k])
        except Exception, e:
            print e


class AimResponse(models.Model):
    response_code = models.IntegerField(verbose_name='Response Code', null=True)
    response_subcode = models.IntegerField(verbose_name='Response Subcode', null=True)
    response_reason_code = models.IntegerField(verbose_name='Response Reason Code', null=True)
    response_reason_text = models.CharField(max_length=512, verbose_name='Response Reason Text', null=True)
    transaction_id = models.CharField(max_length=32, verbose_name='Transaction ID', null=True, db_index=True)
    invoice_number = models.CharField(max_length=64, verbose_name='Invoice Number', null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Amount', null=True)
    transaction_type = models.CharField(max_length=32, verbose_name='Transaction Type', null=True)
    email_address = models.CharField(max_length=50, verbose_name='Email Address', null=True)
    data = BlowfishField(key=settings.BILLING_CARDS_CRYPTO_KEY, null=True)

    def list_data(self):
        try:
            keys = self.data.keys()
            keys.sort()
            for k in keys:
                yield k.replace('_', ' '), self.data[k]
        except Exception, e:
            print e


class AimTransaction(models.Model):
    timestamp = models.DateTimeField(default=datetime.now, db_index=True)
    transaction_type = models.CharField(max_length=32, null=True)
    transaction_id = models.CharField(max_length=32, null=True, db_index=True)
    response_code = models.IntegerField(null=True)
    response_subcode = models.IntegerField(null=True)
    email = models.CharField(max_length=50, db_index=True, null=True)
    user = models.ForeignKey(User, null=True)
    card_type = models.CharField(max_length=10, db_index=True, null=True)
    card_num = models.CharField(max_length=10, db_index=True, null=True)
    request = models.OneToOneField(AimRequest)
    response = models.OneToOneField(AimResponse)


def aim_logger(aim_request, aim_response):
    try:
        aim_request = aim_request or {}
        amount = aim_request.get('x_amount')
        if amount:
            amount = decimal.Decimal('%s' % amount)
            aim_request['x_amount'] = '%s' % aim_request['x_amount']
        if 'x_tax' in aim_request:
            aim_request['x_tax'] = '%s' % aim_request['x_tax']
        request = AimRequest(
            type = aim_request.get('x_type'),
            amount = amount,
            transaction_id = aim_request.get('x_trans_id'),
            data = aim_request,
        ) 
        request.save()

        def _get(d, *args):
            r = {}
            for k in args:
                r[k] = d[k]
            return r

        response = AimResponse(**_get(aim_response._as_dict, 'response_code', 'response_subcode', 
                                      'response_reason_code', 'response_reason_text', 
                                      'transaction_id', 'invoice_number', 'amount', 'transaction_type', 
                                      'email_address'))
        response.data = aim_response._as_dict
        response.save()

        def get_user(email):
            if not email:
                return None
            for u in User.objects.filter(email__iexact=email):
                return u
            return None

        card_num = aim_request.get('x_card_num', '')[-4:]

        AimTransaction(
            transaction_type = aim_request.get('x_type'),
            transaction_id = response.data.get('transaction_id'),
            response_code = response.data.get('response_code'),
            response_subcode = response.data.get('response_subcode'),
            email = response.data.get('email_address'),
            user = get_user(response.data.get('email_address')),
            card_type = aim_response._as_dict.get('card_type'),
            card_num = card_num,
            request = request,
            response = response,
        ).save()
    except:
        logging.error('', exc_info=sys.exc_info())
