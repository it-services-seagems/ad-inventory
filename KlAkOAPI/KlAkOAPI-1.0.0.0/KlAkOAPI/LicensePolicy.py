#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkLicensePolicy (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def IsLimitedMode(self, nFunctionality):
        data = {'nFunctionality': nFunctionality}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicensePolicy.IsLimitedMode'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetTotalLicenseCount(self, nFunctionality):
        data = {'nFunctionality': nFunctionality}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicensePolicy.GetTotalLicenseCount'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetFreeLicenseCount(self, nFunctionality):
        data = {'nFunctionality': nFunctionality}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicensePolicy.GetFreeLicenseCount'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetLimitedModeTest(self, bLimited, eFunctionality):
        data = {'bLimited': bLimited, 'eFunctionality': eFunctionality}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicensePolicy.SetLimitedModeTest'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SetTotalLicenseCountTest(self, eFunctionality, nCount):
        data = {'eFunctionality': eFunctionality, 'nCount': nCount}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicensePolicy.SetTotalLicenseCountTest'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SetUsedLicenseCountTest(self, eFunctionality, nCount):
        data = {'eFunctionality': eFunctionality, 'nCount': nCount}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicensePolicy.SetUsedLicenseCountTest'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

