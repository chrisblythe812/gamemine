from django.utils.unittest import TestCase

from endiciapy import Endicia
from endiciapy.enums import ImageFormat, MailClass, MailpieceShape, LabelType, LabelSize, SortType


class EndiciaTests(TestCase):
    def setUp(self):
        self.endicia = Endicia(None, None, None, test_mode=True)

    def test_get_postage_label(self):
        # Outgoing mail label
        reply_postage = False
        description = "Rental Mailing Shipping Label"

        res_outgoing = self.endicia.get_postage_label(
            type=LabelType.DestinationConfirm,
            size=LabelSize.Dymo30384,
            image_format=ImageFormat.GIF,
            mail_class=MailClass.First,
            date_advance=7,
            weight=3.5,
            mailpiece_shape=MailpieceShape.Letter,
            machinable=True,
            sort_type=SortType.SinglePiece,
            include_postage=True,
            show_return_address=False,
            reply_postage=reply_postage,
            stealth=False,
            signature_waiver=True,
            no_weekend_delivery=False,
            no_holiday_delivery=True,
            return_to_sender=True,
            barcode_format="PLATNET Code, 14",
            cost_center=1,
            description=description,
            reference_id="Rent",
            partner_customer_id="12345678",
            partner_transaction_id="87654321",
            to={
                "name": "Test Name",
                "address1": "1 Test St",
                "address2": "",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "05105-123",
                "zip4": "1234",
                "delivery_point": "00",
            },
            frm={
                "city": u"DELRAY BEACH",
                "name": "GAMEMINE",
                "postal_code": u"33482-9901",
                "state": u"FL",
                "zip4": u"9901"
            },
            return_address="PO BOX 6487",
            postage_price=True)

        self.assertTrue(res_outgoing.Base64LabelImage)

        # Incoming mail label
        reply_postage = True

        res_incoming = self.endicia.get_postage_label(
            type=LabelType.DestinationConfirm,
            size=LabelSize.Dymo30384,
            image_format=ImageFormat.GIF,
            mail_class=MailClass.First,
            date_advance=7,
            weight=3.5,
            mailpiece_shape=MailpieceShape.Letter,
            machinable=True,
            sort_type=SortType.SinglePiece,
            include_postage=True,
            show_return_address=False,
            reply_postage=reply_postage,
            stealth=False,
            signature_waiver=True,
            no_weekend_delivery=False,
            no_holiday_delivery=True,
            return_to_sender=True,
            barcode_format="PLATNET Code, 14",
            cost_center=1,
            description=description,
            reference_id="Rent",
            partner_customer_id="12345678",
            partner_transaction_id="87654321",
            to={
                "name": "Test Name",
                "address1": "1 Test St",
                "address2": "",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "05105-123",
                "zip4": "1234",
                "delivery_point": "00",
            },
            frm={
                "city": u"DELRAY BEACH",
                "name": "GAMEMINE",
                "postal_code": u"33482-9901",
                "state": u"FL",
                "zip4": u"9901"
            },
            return_address="PO BOX 6487",
            postage_price=True)


        self.assertNotEqual(res_incoming.Base64LabelImage,
                            res_outgoing.Base64LabelImage)

    def test_status_request(self):
        resp = self.endicia.status_request(12345)
        self.assertEqual(resp.StatusList.PICNumber.PICNumber, 12345)

        resp = self.endicia.status_request(12345, 54321)
        self.assertEqual(resp.StatusList[0].PICNumber, 12345)
        self.assertEqual(resp.StatusList[1].PICNumber, 54321)

        self.endicia.test_status_response = "D"
        resp = self.endicia.status_request(12345)
        self.assertEqual(resp.StatusList.PICNumber.StatusCode, "D")
