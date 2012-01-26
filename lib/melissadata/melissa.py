from logging import debug  #@UnusedImport
import sys

from errors import MelissaAddressError, ADDRESS_ERROR_CODES, MelissaNameError, NAME_ERROR_CODES
from melissadata.errors import MelissaPhoneError

TEST_MODE = False


class Melissa:
    def __init__(self, conf):
        self.conf = conf
        lib_path = conf.get('lib_path')
        if lib_path:
            sys.path = lib_path.split(':') + sys.path

    def _get_mdAddr(self):
        if hasattr(self, '_mdAddr'):
            return self._mdAddr

        import mdAddrPythonWrapper

        self._mdAddr = mdAddrPythonWrapper.mdAddr()
        self._mdAddr.SetLicenseString(self.conf['address']['api_key'])
        self._mdAddr.SetPathToUSFiles(self.conf['address']['data_path'])
        if self._mdAddr.InitializeDataFiles() != 0:
            raise Exception("Melissa Initialize Error: %s", self._mdAddr.GetInitializeErrorString())

        return self._mdAddr

    def _get_mdZip(self):
        if hasattr(self, '_mdZip'):
            return self._mdZip

        import mdAddrPythonWrapper

        self._mdZip = mdAddrPythonWrapper.mdZip()
        self._mdZip.SetLicenseString(self.conf['address']['api_key'])
        res = self._mdZip.Initialize(self.conf['address']['data_path'], self.conf['address']['data_path'], self.conf['address']['data_path'])
        if res != 0:
            raise Exception("Melissa Initialize Error: %s", self._mdZip.GetInitializeErrorString())

        return self._mdZip

    def _get_mdName(self):
        if hasattr(self, '_mdName'):
            return self._mdName

        import mdNamePythonWrapper

        self._mdName = mdNamePythonWrapper.mdName()
        self._mdName.SetLicenseString(self.conf['name']['api_key'])
        self._mdName.SetPathToNameFiles(self.conf['name']['data_path'])
        if self._mdName.InitializeDataFiles() != 0:
            raise Exception("Melissa Initialize Error: %s", self._mdName.GetInitializeErrorString())

        return self._mdName

    def _get_mdPhone(self):
        if hasattr(self, '_mdPhone'):
            return self._mdPhone

        import mdPhonePythonWrapper

        self._mdPhone = mdPhonePythonWrapper.mdPhone()
        self._mdPhone.SetLicenseString(self.conf['phone']['api_key'])
        res = self._mdPhone.Initialize(self.conf['phone']['data_path'])
        if res != 0:
            raise Exception("Melissa Initialize Error: %s", self._mdPhone.GetInitializeErrorString())

        return self._mdPhone

    def inaccurate_address(self, quiet=False, **kwargs):
        if TEST_MODE:
            kwargs['city'] = "New New York"
            return kwargs
        mdAddr = self._get_mdAddr()

        address1 = (kwargs.get('address1') or '').encode('ascii', 'ignore')
        address2 = (kwargs.get('address2') or '').encode('ascii', 'ignore')
        city = (kwargs.get('city') or '').encode('ascii', 'ignore')
        state = (kwargs.get('state') or '').encode('ascii', 'ignore')
        zip = (kwargs.get('zip_code') or '').encode('ascii', 'ignore')

        #debug('Trying to inaccurate address: %s %s, %s %s %s...', address1, address2, city, state, zip)

        mdAddr.ClearProperties()
        mdAddr.SetAddress(address1)
        mdAddr.SetAddress2(address2)
        mdAddr.SetCity(city)
        mdAddr.SetState(state)
        mdAddr.SetZip(zip)

        mdAddr.VerifyAddress()
        ResultsString = mdAddr.GetResults()
        res = {
            "address1": mdAddr.GetAddress(),
            "address2": ' '.join([mdAddr.GetAddress2(), mdAddr.GetSuite()]).strip(),
            "city": mdAddr.GetCity(),
            "state": mdAddr.GetState(),
            "county": mdAddr.GetCountyName(),
            "zip_code": '-'.join(filter(None, [mdAddr.GetZip(), mdAddr.GetPlus4()])),
        }
        if not quiet and ResultsString.find('AS01') == -1 and ResultsString.find('AS02') == -1:
#            debug('ResultsString: %s', ResultsString)
#            debug(kwargs)
#            debug(res)
            raise MelissaAddressError(ResultsString)
        #debug('Got address: %s | %s, %s %s %s...', res['address1'], res['address2'], res['city'], res['state'], res['zip_code'])
        return res

    def get_coords_by_zip_code(self, zip_code):
        if TEST_MODE:
            return 0, 0
        mdZip = self._get_mdZip()
        zip_code = str(zip_code).split('-')[0]
        if not mdZip.FindZip(zip_code, 0):
            return None
        return mdZip.GetLatitude(), mdZip.GetLongitude()

    def compute_distance(self, p1, p2):
        if TEST_MODE:
            return 0
        mdZip = self._get_mdZip()

        def normalize(p):
            return p if type(p) is tuple else self.get_coords_by_zip_code(p)

        p1, p2 = normalize(p1), normalize(p2)
        if not p1 or not p2:
            return None

        distance = mdZip.ComputeDistance(*(map(float, p1 + p2)))
        return distance if distance != 9999 else None

    def inaccurate_name(self, **kwargs):
        if TEST_MODE:
            return kwargs
        mdName = self._get_mdName()

        mdName.ClearProperties()
        mdName.SetFirstNameSpellingCorrection(True)
        mdName.SetPrimaryNameHint(4)

        if 'full_name' in kwargs:
            full_name = (kwargs['full_name'] or '').encode('ascii', 'ignore')
#            debug('Trying to inaccurate name: %s...', full_name)
            mdName.SetFullName(full_name)
        else:
            first_name = (kwargs.get('first_name') or '').encode('ascii', 'ignore')
            last_name = (kwargs.get('last_name') or '').encode('ascii', 'ignore')
#            debug('Trying to inaccurate name: %s %s...', first_name, last_name)
            mdName.SetFullName(' '.join([first_name, last_name]))


        mdName.Parse()

#        ResultsString = mdName.GetResults()
#        if ResultsString.startswith('NE'):
#            raise MelissaAddressError(ResultsString)
        res = {
            'first_name': mdName.GetFirstName(),
            'last_name': mdName.GetLastName(),
        }
#        debug('Result name: %s %s...', res['first_name'], res['last_name'])
        return res

    def inaccurate_phone(self, phone, zip=None):
        if TEST_MODE:
            return phone
        mdPhone = self._get_mdPhone()
        if not mdPhone.Lookup(phone.encode('ascii', 'ignore'), (zip or '').encode('ascii', 'ignore')):
            return phone
#            raise MelissaPhoneError(mdPhone.GetErrorCode())
        mdPhone.Lookup(phone.encode('ascii', 'ignore'), (zip or '').encode('ascii', 'ignore'))
        ext = mdPhone.GetExtension()
        ext = ' ext. %s' % ext if ext else ''
        area = mdPhone.GetAreaCode()
        if area:
            return '(%s) %s-%s%s' % (area, mdPhone.GetPrefix(), mdPhone.GetSuffix(), ext)
        else:
            return '%s-%s%s' % (mdPhone.GetPrefix(), mdPhone.GetSuffix(), ext)

#######################################################################################################

    def test2(self):
        print self.inaccurate_address(address1='210 DEVONSHIRE DR',
#                                      address2='UNIT 10',
                                      zip_code='28333-0117')

    def test(self):
        try:
            print self.inaccurate_address(address1='1305 east 18 street apt. 1a', city='brooklyn', zip_code='11229')
        except Exception, e:
            print e

        mdAddr = self._get_mdAddr()
        print "==============================================="
        print "            BuildNumber: ", mdAddr.GetBuildNumber()
        print "          Database Date: ", mdAddr.GetDatabaseDate()
        print " DatabaseExpirationDate: ", mdAddr.GetExpirationDate()
        print "===============================================\n"

#        {'city': 'Canton', 'address1': '2574 Ocelot St NE', 'address2': '', 'county': 'Stark', 'state': 'OH', 'zip_code': '44721-2142'}

#        mdAddr.SetAddress('1305 east 18 street apt. 1a')
#        mdAddr.SetCity('brooklyn');
#        mdAddr.SetZip('11229')

        mdAddr.SetAddress('124 SHERMAN AVE APT BSMS')
        mdAddr.SetCity('');
        mdAddr.SetZip('10034-5513')


        mdAddr.VerifyAddress()
        print "\n============AddressObject Outputs=============\n"
        print "\n"
        print "          Company: ", mdAddr.GetCompany()
        print "          Address: ", mdAddr.GetAddress()
        print "         Address2: ", mdAddr.GetAddress2()
        print "            Suite: ", mdAddr.GetSuite()
        print "             City: ", mdAddr.GetCity()
        print "            State: ", mdAddr.GetState()
        print "          ZipCode: ", mdAddr.GetZip()
        print "            Plus4: ", mdAddr.GetPlus4()

        ResultsString = mdAddr.GetResults()
        print ResultsString

        if (ResultsString.find("AS01")!= -1) or (ResultsString.find("AS02")!= -1):
        # the address was verified
            if (ResultsString.find("AS01")!= -1):
                print " AS01: Address Matched to Postal Database and is deliverable"
            elif (ResultsString.find("AS02")!= -1):
                print " AS02: Address matched to USPS database but a suite was missing or invalid"

        if ResultsString in ADDRESS_ERROR_CODES:
            raise MelissaAddressError(ResultsString)

        ########################################

        mdName = self._get_mdName()

        print "======================================"
        print "      NAME OBJECT PYTHON EXAMPLE"
        print "======================================"
        print "             BuildNumber: ", mdName.GetBuildNumber()
        print "           Database Date: ", mdName.GetDatabaseDate()
        print "Database Expiration Date: ", mdName.GetDatabaseExpirationDate()
        print " License Expiration Date: ", mdName.GetLicenseExpirationDate()
        print "======================================\n"

        mdName.SetFirstNameSpellingCorrection(True)
        mdName.SetPrimaryNameHint(4)

        mdName.SetFullName('jonh doe')
        mdName.Parse()

        print "      Prefix: ", mdName.GetPrefix()
        print "  First Name: ", mdName.GetFirstName()
        print " Middle Name: ", mdName.GetMiddleName()
        print "   Last Name: ", mdName.GetLastName()
        print "      Suffix: ", mdName.GetSuffix()
        print "      Gender: ", mdName.GetGender()
        print "     Prefix2: ", mdName.GetPrefix2()
        print " First Name2: ", mdName.GetFirstName2()
        print "Middle Name2: ", mdName.GetMiddleName2()
        print "  Last Name2: ", mdName.GetLastName2()
        print "     Suffix2: ", mdName.GetSuffix2()
        print "     Gender2: ", mdName.GetGender2()
        print "  Salutation: ", mdName.GetSalutation()
        print "\n"
        print "Results Codes... "
        ResultsString = mdName.GetResults()
        print ResultsString

        if ResultsString in NAME_ERROR_CODES:
            raise MelissaNameError(ResultsString)

        #################################################################

        for z in ['33482-9901', '08906-1500', '89193-8199']:
            print 'Coords for %s: %s' % (z, self.get_coords_by_zip_code(z))

        z1, z2 = '89501', '89434-8090'
        print "The distance between %s and %s is %d miles" % (z1, z2, self.compute_distance(z1, z2))

        z1, z2 = '59401-2008', '89434-8090'
        print "The distance between %s and %s is %d miles" % (z1, z2, self.compute_distance(z1, z2))

        ##################################################################

        def test_phone(phone, zip=None):
            try:
                print '%s --> %s' % (phone, self.inaccurate_phone(phone, zip))
            except MelissaPhoneError, e:
                print 'Error: %s' % e
        test_phone('(786) 425-1900 2343')
        test_phone('786-425-1900')
        test_phone('786425-1900')
        test_phone('(787)4251900', '33131-1506')
        test_phone('7864')
