from logging import debug  #@UnusedImport
import itertools
import random


RESPONSE_FIELDS = (
    ("response_code", "Response Code", int),
    ("response_subcode", "Response Subcode", int),
    ("response_reason_code", "Response Reason Code", int),
    ("response_reason_text", "Response Reason Text"),
    ("authorization_code", "Authorization Code"),
    ("avs_response", "AVS Response"),
    ("transaction_id", "Transaction ID"),
    ("invoice_number", "Invoice Number"),
    ("description", "Description"),
    ("amount", "Amount"),
    ("method", "Method"),
    ("transaction_type", "Transaction Type"),
    ("customer_id", "Customer ID"),
    ("first_name", "First Name"),
    ("last_name", "Last Name"),
    ("company", "Company"),
    ("address", "Address"),
    ("city", "City"),
    ("state", "State"),
    ("zip_code", "ZIP Code"),
    ("country", "Country"),
    ("phone", "Phone"),
    ("fax", "Fax"),
    ("email_address", "Email Address"),
    ("ship_to_first_name", "Ship To First Name"),
    ("ship_to_last_name", "Ship To Last Name"),
    ("ship_to_company", "Ship To Company"),
    ("ship_to_address", "Ship To Address"),
    ("ship_to_city", "Ship To City"),
    ("ship_to_state", "Ship To State"),
    ("ship_to_zip_code", "Ship To ZIP Code"),
    ("ship_to_country", "Ship To Country"),
    ("tax", "Tax"),
    ("duty", "Duty"),
    ("freight", "Freight"),
    ("tax_exempt", "Tax Exempt"),
    ("purchase_order_number", "Purchase Order Number"),
    ("md5_hash", "MD5 Hash"),
    ("card_code_response", "Card Code Response"),
    ("cardholder_authentication_verification_response", "Cardholder Authentication Verification Response"),
    ("split_tender_id", "Split Tender ID"),
    ("requested_amount", "Requested Amount"),
    ("balance_on_card", "Balance On Card"),
    ("account_number", "Account Number"),
    ("card_type", "Card Type"),
)
RESPONSE_FIELDS_DICT = dict([x[:2] for x in RESPONSE_FIELDS])

AVS_CODES = {
    "A": "Address (Street) matches, ZIP does not",
    "B": "Address information not provided for AVS check",
    "E": "AVS error",
    "G": "Non-U.S. Card Issuing Bank",
    "N": "No Match on Address (Street) or ZIP",
    "P": "AVS not applicable for this transaction",
    "R": "Retry - System unavailable or timed out",
    "S": "Service not supported by issuer",
    "U": "Address information is unavailable",
    "W": "Nine digit ZIP matches, Address (Street) does not",
    "X": "Address (Street) and nine digit ZIP match",
    "Y": "Address (Street) and five digit ZIP match",
    "Z": "Five digit ZIP matches, Address (Street) does not",
}


class AimResponse(object):
    def __init__(self, response_array):
        self._data = response_array
        self._as_dict = {}
        response_array = itertools.chain(response_array, itertools.repeat(None))
        for k, v in itertools.izip(RESPONSE_FIELDS, response_array):
            if len(k) == 3:
                v = k[2](v)
            self._as_dict[k[0]] = v
            setattr(self, k[0], v)

    def _get_field_display(self, field_name, align=None):
        v = RESPONSE_FIELDS_DICT[field_name]
        if align:
            v = " " * (align - len(v)) + v
        return "%s: %s" % (v, getattr(self, field_name))

    def __str__(self):
        _ = self._get_field_display
        m_len = max(map(lambda x: len(x[0]), RESPONSE_FIELDS))
        return "\n".join(map(lambda x: _(x[0], m_len), RESPONSE_FIELDS))

    @staticmethod
    def format(d):
        for k in RESPONSE_FIELDS:
            v = d.get(k[0])
            if k[0] == "avs_response" and v in AVS_CODES:
                v += " - " + AVS_CODES[v]
            yield k[1], v


class TestAimResponse(AimResponse):
    def __init__(self, data, response_code=1):
        response_subcode = response_reason_code = response_code
        response_reason_text = {
            1: "This transaction has been approved",
            2: "This transaction has been declined",
            3: "A valid amount is required"
        }[response_code]
        transaction_id = "TEST-" + "".join(
            map(str, [random.randint(0, 9) for _x in range(10)]))
        email = data.get("x_email", "email@domain.com")
        tax = data.get("x_tax", "0.00")
        x_type = data["x_type"]

        dummy_response = [
            response_code,
            response_subcode,
            response_reason_code,
            response_reason_text,
            "", "",
            data.get("x_trans_id", transaction_id),
            data.get("x_invoice_num", ""),
            data.get("x_description", ""),
            data.get("x_amount", ""),
            data.get("x_method", ""),
            x_type,
            "",
            data.get("x_first_name", ""),
            data.get("x_last_name", ""),
            "",
            data.get("x_address", ""),
            data.get("x_city", ""),
            data.get("x_state", ""),
            data.get("x_zip", ""),
            data.get("x_country", ""),
            "", "",
            email,
            data.get("x_ship_to_first_name", ""),
            data.get("x_ship_to_last_name", ""),
            "",
            data.get("x_ship_to_address", ""),
            data.get("x_ship_to_city", ""),
            data.get("x_ship_to_state", ""),
            data.get("x_ship_to_zip", ""),
            data.get("x_ship_to_country", ""),
            tax,
            "", "", "", "",
            "1E94988AC38F5024DE151028DD83D706",
            "", "", "", "", "", "", "", "", "", "", "", "",
            "XXXX1111",
            "Visa",
            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        dummy_response = [str(item) for item in dummy_response]

        super(TestAimResponse, self).__init__(dummy_response)
