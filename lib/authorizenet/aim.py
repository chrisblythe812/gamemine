from pprint import pformat
import urllib2
import urllib
import logging

from response import AimResponse, TestAimResponse

logger = logging.getLogger(__name__)


class AIM(object):
    def __init__(self, gateway, api_login_id, trans_key, test_mode=False,
                 test_response_code=1, **kwargs):
        self.gateway = gateway
        self.api_login_id = api_login_id
        self.trans_key = trans_key
        self.test_mode = test_mode
        self.test_response_code = test_response_code

    def __post(self, params):
        data = {
            'x_login': self.api_login_id,
            'x_tran_key': self.trans_key,
            'x_delim_data': 'TRUE',
            'x_delim_char': '|',
#            'x_relay_response': 'FALSE',
        }
        data.update(params)
        logger.debug('Data posted to authorize.net:\n%s', pformat(data))
        if not self.test_mode:
            response = urllib2.urlopen(self.gateway, urllib.urlencode(data.items())).read().split('|')
            res = AimResponse(response)
        else:
            data['x_test_request'] = 'TRUE'
            res = TestAimResponse(data, self.test_response_code)
        logger.debug('Authorize.net response:\n%s', res)
        return res


    def test(self, number, exp, ccv=None):
        print self.authorize(number, exp, ccv)

    def __prepare_personal_data(self, billing, shipping):
        data = {}
        def put(id, k, d, default=None):
            v = d.get(k, default)
            if v is not None: data[id] = v
        if billing:
            put('x_first_name', 'first_name', billing)
            put('x_last_name', 'last_name', billing)
            put('x_address', 'address1', billing)
            put('x_city', 'city', billing)
            put('x_state', 'state', billing)
            put('x_zip', 'zip_code', billing)
            put('x_country', 'country', billing, 'USA')
        if shipping:
            put('x_ship_to_first_name', 'first_name', shipping)
            put('x_ship_to_last_name', 'last_name', shipping)
            put('x_ship_to_address', 'address1', shipping)
            put('x_ship_to_city', 'city', shipping)
            put('x_ship_to_state', 'state', shipping)
            put('x_ship_to_zip', 'zip_code', shipping)
            put('x_ship_to_country', 'country', shipping, 'USA')
        return data

    def __request(self, type, number, exp, code='', amount=0.01, billing=None, shipping=None,
                  invoice_num=None, description=None, trans_id=None, **kwargs):
        data = {
            'x_type': type,
            'x_recurring_billing': 'NO',
            'x_amount': amount,
            'x_method': 'CC',
            'x_card_num': number,
            'x_exp_date': exp,
            'x_card_code': code,
        }
        data.update(self.__prepare_personal_data(billing, shipping))
        if invoice_num: data['x_invoice_num'] = invoice_num
        if description: data['x_description'] = description
        if trans_id: data['x_trans_id'] = trans_id
        data.update(kwargs)
        if 'x_customer_ip' in data:
            x_customer_ip = data['x_customer_ip']
            if not x_customer_ip or x_customer_ip == '127.0.0.1':
                del data['x_customer_ip']
        res = self.__post(data)
        return res

    def authorize(self, amount, number, exp, code='', billing=None,
                  shipping=None, invoice_num=None, description=None, **kwargs):
        """
        Authorizes transaction

        Args:
            ``amount``: Money amount (e.g. Decimal("8.99"))
            ``number``: Card number (e.g. "4111111111111111")
            ``exp``: Card expires (e.g. "1/12")
            ``code``: CVV code (e.g. "123")
            ``billing``: Dictionary with billing data (e.g.
                {
                    "address1": u"1 Test St",
                    "address2": u"",
                    "city": u"Test City",
                    "code": u"123",
                    "country": "USA",
                    "exp_month": u"1",
                    "exp_year": u"2012",
                    "first_name": u"Roman",
                    "last_name": u"Dolgiy",
                    "number": u"4111111111111111",
                    "state": u"AZ",
                    "type": u"visa",
                    "zip_code": u"05105",
                })
            ``spipping``: Dictionary with shipping data (e.g.
                {
                    "address1": u"1 Test St",
                    "address2": u"",
                    "city": u"Test City",
                    "confirm_password": u"19891010",
                    "country": "USA",
                    "email": u"roman@bravetstudio.com",
                    "first_name": u"Roman",
                    "how_did_you_hear": u"2",
                    "last_name": u"Dolgiy",
                    "password": u"19891010",
                    "state": u"AZ",
                    "username": u"t0ster",
                    "zip_code": u"05105",
                })
            ``invoice_num``: e.g. "RENT_NEW_44596"
            ``description``: e.g. "Monthly Membership - Aug 11, 2011 - Sep 11, 2011"
        """
        logger.debug('Authorizing $%s from %s (%s)...', amount, number, invoice_num or '--')
        res = self.__request('AUTH_ONLY', number, exp, code, amount, billing, shipping, invoice_num, description, **kwargs)
        logger.debug('Response Code: %s, %s', res.response_code, res.response_subcode)
        return res

    def capture(self, amount, number, exp, code='', billing=None, shipping=None, invoice_num=None, description=None, **kwargs):
        logger.debug('Capturing $%s from %s (%s)...', amount, number, invoice_num or '--')
        res = self.__request('AUTH_CAPTURE', number, exp, code, amount, billing, shipping, invoice_num, description, **kwargs)
        logger.debug('Response Code: %s, %s', res.response_code, res.response_subcode)
        return res

    def prior_auth_capture(self, amount, trans_id, billing=None, shipping=None, **data):
        logger.debug('Prior authorized capture of $%s (Transaction ID: %s)...', amount, trans_id)
        data.update({
            'x_type': 'PRIOR_AUTH_CAPTURE',
            'x_amount': amount,
            'x_trans_id': trans_id,
        })
        data.update(self.__prepare_personal_data(billing, shipping))
        res = self.__post(data)
        logger.debug('Response Code: %s, %s', res.response_code, res.response_subcode)
        return res

    def void(self, trans_id, data={}):
        logger.debug('Voiding transaction: %s...', trans_id)
        data = {
            'x_type': 'VOID',
            'x_trans_id': trans_id,
        }
        res = self.__post(data)
        logger.debug('Response Code: %s, %s', res.response_code, res.response_subcode)
        return res

    def refund(self, trans_id, amount, credit_card_number, billing=None, shipping=None, **aim_data):
        logger.debug('Refunding transaction: %s...', trans_id)
        aim_data.update({
            'x_type': 'CREDIT',
            'x_amount': amount,
            'x_trans_id': trans_id,
            'x_card_num': credit_card_number,
        })
        aim_data.update(self.__prepare_personal_data(billing, shipping))
        logger.debug(aim_data)
        res = self.__post(aim_data)
        logger.debug('Response Code: %s, %s', res.response_code, res.response_subcode)
        return res
