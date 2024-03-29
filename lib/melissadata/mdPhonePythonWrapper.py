#@PydevCodeAnalysisIgnore
# This file was automatically generated by SWIG (http://www.swig.org).
# Version 1.3.36
#
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _mdPhonePythonWrapper
import new
new_instancemethod = new.instancemethod
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'PySwigObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static) or hasattr(self,name):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

class mdPhone:
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, mdPhone, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, mdPhone, name)
    __repr__ = _swig_repr
    ErrorNone = _mdPhonePythonWrapper.mdPhone_ErrorNone
    ErrorOther = _mdPhonePythonWrapper.mdPhone_ErrorOther
    ErrorOutOfMemory = _mdPhonePythonWrapper.mdPhone_ErrorOutOfMemory
    ErrorRequiredFileNotFound = _mdPhonePythonWrapper.mdPhone_ErrorRequiredFileNotFound
    ErrorFoundOldFile = _mdPhonePythonWrapper.mdPhone_ErrorFoundOldFile
    ErrorDatabaseExpired = _mdPhonePythonWrapper.mdPhone_ErrorDatabaseExpired
    ErrorLicenseExpired = _mdPhonePythonWrapper.mdPhone_ErrorLicenseExpired
    Local = _mdPhonePythonWrapper.mdPhone_Local
    Remote = _mdPhonePythonWrapper.mdPhone_Remote
    Auto = _mdPhonePythonWrapper.mdPhone_Auto
    On = _mdPhonePythonWrapper.mdPhone_On
    Off = _mdPhonePythonWrapper.mdPhone_Off
    def __init__(self, *args): 
        this = apply(_mdPhonePythonWrapper.new_mdPhone, args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _mdPhonePythonWrapper.delete_mdPhone
    __del__ = lambda self : None;
    def Initialize(*args): return apply(_mdPhonePythonWrapper.mdPhone_Initialize, args)
    def GetInitializeErrorString(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetInitializeErrorString, args)
    def SetLicenseString(*args): return apply(_mdPhonePythonWrapper.mdPhone_SetLicenseString, args)
    def GetBuildNumber(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetBuildNumber, args)
    def GetDatabaseDate(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetDatabaseDate, args)
    def Lookup(*args): return apply(_mdPhonePythonWrapper.mdPhone_Lookup, args)
    def CorrectAreaCode(*args): return apply(_mdPhonePythonWrapper.mdPhone_CorrectAreaCode, args)
    def ComputeDistance(*args): return apply(_mdPhonePythonWrapper.mdPhone_ComputeDistance, args)
    def ComputeBearing(*args): return apply(_mdPhonePythonWrapper.mdPhone_ComputeBearing, args)
    def GetAreaCode(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetAreaCode, args)
    def GetNewAreaCode(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetNewAreaCode, args)
    def GetPrefix(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetPrefix, args)
    def GetSuffix(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetSuffix, args)
    def GetExtension(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetExtension, args)
    def GetCity(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetCity, args)
    def GetState(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetState, args)
    def GetCountyFips(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetCountyFips, args)
    def GetCountyName(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetCountyName, args)
    def GetMsa(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetMsa, args)
    def GetPmsa(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetPmsa, args)
    def GetTimeZone(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetTimeZone, args)
    def GetTimeZoneCode(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetTimeZoneCode, args)
    def GetCountryCode(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetCountryCode, args)
    def GetLatitude(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetLatitude, args)
    def GetLongitude(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetLongitude, args)
    def GetDistance(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetDistance, args)
    def GetStatusCode(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetStatusCode, args)
    def GetErrorCode(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetErrorCode, args)
    def GetResults(*args): return apply(_mdPhonePythonWrapper.mdPhone_GetResults, args)
mdPhone_swigregister = _mdPhonePythonWrapper.mdPhone_swigregister
mdPhone_swigregister(mdPhone)



