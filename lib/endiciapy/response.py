import datetime
import random
import string

from xml_to_dict import xml_to_dict

from endiciapy import fixtures


class Object:
    pass


def _extend(obj, d):
    for k, v in d.items():
        if isinstance(v, list):
            value = []
            for item in v:
                o = Object()
                _extend(o, item)
                value.append(o)
        elif isinstance(v, dict):
            value = Object()
            _extend(value, v)
        else:
            value = v
        setattr(obj, k, value)


class EndiciaResponse:
    def __init__(self, response):
        self._xml = response
        self._dict = xml_to_dict(response)
        _extend(self, self._dict.values()[0])

    def __str__(self):
        return self._xml


class TestEndiciaResponse:
    def __init__(self, reply_postage):
        _ = (reply_postage and fixtures.INCOMING_LABEL_BASE64 or
             fixtures.OUTGOING_LABEL_BASE64)
        Base64LabelImage = _
        PIC = self._generate_tracking_number()

        self._dict = {
            u"LabelRequestResponse": {
                u"Base64LabelImage": Base64LabelImage,
                u"CostCenter": u"1",
                u"FinalPostage": u"1.04",
                u"PIC": PIC,
                u"PostageBalance": u"0.0",
                u"PostagePrice": {u"Fees": {u"CertificateOfMailing": u"0",
                                            u"CertifiedMail": u"0",
                                            u"CollectOnDelivery": u"0",
                                            u"CriticalMail": u"0",
                                            u"DeliveryConfirmation": u"0",
                                            u"ElectronicReturnReceipt": u"0",
                                            u"InsuredMail": u"0",
                                            u"MerchandiseReturn": u"0",
                                            u"OpenAndDistribute": u"0",
                                            u"RegisteredMail": u"0",
                                            u"RestrictedDelivery": u"0",
                                            u"ReturnReceipt": u"0",
                                            u"ReturnReceiptForMerchandise": u"0",
                                            u"SignatureConfirmation": u"0",
                                            u"SpecialHandling": u"0"},
                                  u"MailClass": u"First",
                                  u"Postage": {u"IntraBMC": u"false",
                                               u"MailService": u"First-Class Mail",
                                               u"Pricing": u"Retail",
                                               u"Zone": u"6"
                                           }
                                  },
                u"PostmarkDate": self._generate_postmark_date(),
                u"ReferenceID": u"Rent",
                u"Status": u"0",
                u"TrackingNumber": PIC,
                u"TransactionDateTime": self._generate_transaction_dt(),
                u"TransactionID": u"0"
        }}
        _extend(self, self._dict.values()[0])

    def _generate_transaction_dt(self):
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d%H%M%S")

    def _generate_postmark_date(self):
        _ = datetime.date.today()
        _ += datetime.timedelta(7)
        return _.strftime("%Y%m%d")

    def _generate_tracking_number(self):
        return "".join(random.choice(string.digits) for x in range(25))


class TestEndiciaStatusResponse:
    def __init__(self, request, status="N"):
        _pic_numbers = []
        for pic_number in request["StatusList"]:
            _pic_numbers.append({
                "PICNumber": pic_number["PICNumber"],
                "Status": u"Your item was accepted into the mailstream at 4:29 PM on 07/24/2007 in PALO ALTO CA 94303.",
                "StatusCode": status,  # "N" = New item
                "Test": "Y",
            })
        if len(_pic_numbers) == 1:
            _pic_numbers = {"PICNumber": _pic_numbers[0]}

        self._dict = {
            u"StatusResponse": {
                u"AccountID": request["AccountID"],
                u"ErrorMsg": {},
                u"StatusList": _pic_numbers,
        }}
        _extend(self, self._dict.values()[0])
