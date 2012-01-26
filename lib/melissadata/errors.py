ADDRESS_ERROR_CODES = {
     "AE01": "The Postal Code does not exist",
     "AE02": "An street name match could not be found.",
     "AE03": "The directionals field did not match the post office database.",
     "AE04": "There are no homes on this street.",
     "AE05": "Address matched to multiple records.",
     "AE06": "This address has been identified in the Early Warning System.",
     "AE07": "Minimum required input of address not found.",
     "AE08": "The street address was found but the suite number was not valid.",
     "AE09": "The street address was found but a required suite number is missing.",
     "AE10": "The street number in the input address was not valid.",
     "AE11": "The street number in the input address was missing.",
     "AE12": "The input address PO, RR or HC number was invalid.",
     "AE13": "The input address is missing a PO, RR, or HC Box number.",
     "AE14": "Address Matched to a CMRA Address but the secondary (Private mailbox number) is missing.",
     "AE15": "Address Object is in demo mode.",
     "AE16": "The database has expired. Please update with a fresh database.",    
}


class MelissaAddressError(Exception):
    def __init__(self, code):
        code = code.split(',') or [None]
        self.code = code[0]
        
    def __str__(self):
        if self.code in ADDRESS_ERROR_CODES:
            return ADDRESS_ERROR_CODES[self.code]
        return "The addresss could not be verified..."


NAME_ERROR_CODES = {
    "NE01": "Two names were detected but the FullName string was not in a recognized format.",
    "NE02": "Multiple first names - could not accurately genderize.",
    "NE03": "A vulgarity was detected in the name.",
    "NE04": "The name contained words found on the list of nuisance names [such as Mickey Mouse].",
    "NE05": "The name contained words normally found in a company name.",
    "NE06": "The named contained a non-alphabetic character.",
}


class MelissaNameError(Exception):
    def __init__(self, code):
        self.code = code
        
    def __str__(self):
        if self.code in NAME_ERROR_CODES:
            return NAME_ERROR_CODES[self.code]
        return "The name could not be verified..."


PHONE_ERROR_CODES = {
    "PE01": "Bad Area Code", # The area code does not exist in our database or contains non-numbers.
    "PE02": "Blank Phone Number",  # Phone number was not populated.
    "PE03": "Bad phone number", # Too many or too few digits.
    "PE04": "Multiple Match", # Multiple Match (could not choose between 2 or more area codes as a bad or missing area code was encountered and the distance between the area codes was too close to choose one over the other)
    "PE05": "Bad Prefix", # The prefix does not exist in the database.
    "PE06": "Bad ZIP Code", # An invalid ZIP Code was entered.
}

class MelissaPhoneError(Exception):
    def __init__(self, code):
        self.code = code
        
    def __str__(self):
        if self.code in PHONE_ERROR_CODES:
            return PHONE_ERROR_CODES[self.code]
        return "The phone could not be verified..."
        