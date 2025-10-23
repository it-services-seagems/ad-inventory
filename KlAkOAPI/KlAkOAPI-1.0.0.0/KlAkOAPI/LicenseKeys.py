#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkLicenseKeys (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def InstallKey(self, pKeyInfo):
        data = {'pKeyInfo': pKeyInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.InstallKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UninstallKey(self, pKeyInfo):
        data = {'pKeyInfo': pKeyInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.UninstallKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetKeyData(self, pKeyInfo):
        data = {'pKeyInfo': pKeyInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.GetKeyData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def EnumKeys(self, pFields, pFieldsToOrder, pOptions, lTimeoutSec):
        data = {'pFields': pFields, 'pFieldsToOrder': pFieldsToOrder, 'pOptions': pOptions, 'lTimeoutSec': lTimeoutSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.EnumKeys'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['lKeyCount', 'wstrIterator'])

    def AcquireKeyHosts(self, pInData, pFields, pFieldsToOrder, pOptions, lTimeoutSec):
        data = {'pInData': pInData, 'pFields': pFields, 'pFieldsToOrder': pFieldsToOrder, 'pOptions': pOptions, 'lTimeoutSec': lTimeoutSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.AcquireKeyHosts'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['lKeyCount', 'wstrIterator'])

    def CheckIfSaasLicenseIsValid(self, pInData, bAsCurrent):
        data = {'pInData': pInData, 'bAsCurrent': bAsCurrent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.CheckIfSaasLicenseIsValid'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SaasTryToInstall(self, pInData, bAsCurrent):
        data = {'pInData': pInData, 'bAsCurrent': bAsCurrent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.SaasTryToInstall'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SaasTryToUninstall(self, bCurrent):
        data = {'bCurrent': bCurrent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.SaasTryToUninstall'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def AdjustKey(self, pData):
        data = {'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.AdjustKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DownloadKeyFiles(self, wstrActivationCode):
        data = {'wstrActivationCode': wstrActivationCode}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseKeys.DownloadKeyFiles'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

