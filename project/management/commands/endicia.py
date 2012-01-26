import sys
import decimal
from logging import debug

from django.core.management.base import LabelCommand
from django.conf import settings

from endiciapy import Endicia, ImageFormat, MailClass, MailpieceShape


class Command(LabelCommand):
    def _get_args(self):
        for m in dir(self):
            if m.startswith('do_'):
                yield m[3:]
    
    help = 'Working with endicia'
    label = 'command'

    def handle_label(self, label, **options):
        try:
            method = getattr(self, 'do_' + label)
        except:
            print >>sys.stderr, 'Possible commands are: %s' % ', '.join(self._get_args())
            return
        self._items_cache = {}
        self._missing_items = set()
        method()


    def do_test(self):
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
                
        endicia = Endicia(**settings.ENDICIA_CONF)
        endicia.format_xml = True
        
        print 'Querying label...'        
        res = endicia.get_postage_label(
            weight=7,
            image_format=ImageFormat.GIF,
            mail_class=MailClass.First,
            mailpiece_shape=MailpieceShape.Parcel,
            stealth=False,
            rubber_stamp='CUSTOMER ID: 00000ABC\nORDER # 0000EFGH',
            services={
                'delivery_confirmation': False,
            },
            reference_id='Store',
            description='Buy Shipping Label',
            partner_customer_id='00000ABC',
            partner_transaction_id='0000EFGH',
            to={
                'name': 'MARY WALZ',
                'company': 'ENDICIA',
                'address1': '247 HIGH ST',
                'city': 'PALO ALTO',
                'state': 'CA',
                'postal_code': '94301',
                'zip4': '0000',
                'delivery_point': '00',
                'country': 'United States',
            },
            return_address='PO BOX 6487',            
            frm={
                'name': 'GAMEMINE',
                'city': 'DELRAY BEACH',
                'state': 'FL',
                'postal_code': '33482',
                'zip4': '9901',
            },
            postage_price=True)
        print '    PIC:', res.PIC
        print 'Checking status...'        
        res = endicia.status_request(res.PIC, '9122148008600123456781')
        if isinstance(res.StatusList, list):
            for i in res.StatusList:
                i = i.PICNumber
                print '    %s: %s (%s)' % (i.PICNumber, i.StatusCode, i.Status)
        else:
            i = res.StatusList.PICNumber
            print '    %s: %s (%s)' % (i.PICNumber, i.StatusCode, i.Status)
        print 'DONE'

    def do_get_balance(self):
        endicia = Endicia(**settings.ENDICIA_CONF)
        endicia.format_xml = True
    
        res = endicia.get_account_status()
        print res._xml

    def do_recredit(self):
        endicia = Endicia(**settings.ENDICIA_CONF)
        endicia.format_xml = True
    
        res = endicia.get_account_status()
        #print res._xml
        balance = decimal.Decimal(res.CertifiedIntermediary.PostageBalance)
        debug('Current balance: %s', balance)
        if balance > 100 and balance < 1000000:
            return
        debug('Adding 300.0')
        res = endicia.recredit(300)
        #print res._xml
        balance = decimal.Decimal(res.CertifiedIntermediary.PostageBalance)
        debug('Current balance: %s', balance)
        
