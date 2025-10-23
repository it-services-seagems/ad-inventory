#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkLicenseInfoSync (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def SynchronizeLicInfo(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.SynchronizeLicInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SynchronizeLicInfo2(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.SynchronizeLicInfo2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def TryToUnistallLicense(self, bCurrent):
        data = {'bCurrent': bCurrent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.TryToUnistallLicense'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def IsLicForSaasValid2(self, pKeyInfo, bAsCurrent):
        data = {'pKeyInfo': pKeyInfo, 'bAsCurrent': bAsCurrent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.IsLicForSaasValid2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TryToInstallLicForSaas2(self, pKeyInfo, bAsCurrent):
        data = {'pKeyInfo': pKeyInfo, 'bAsCurrent': bAsCurrent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.TryToInstallLicForSaas2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def IsPCloudKey(self, nProductId):
        data = {'nProductId': nProductId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.IsPCloudKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def IsPCloudKey2(self, pKeyInfo):
        data = {'pKeyInfo': pKeyInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.IsPCloudKey2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AcquireKeysForProductOnHost(self, szwHostName, szwProduct, szwVersion):
        data = {'szwHostName': szwHostName, 'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.AcquireKeysForProductOnHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrActiveKey', 'wstrReservedKey'])

    def AcquireKeysForProductOnHost2(self, szwHostName, szwProduct, szwVersion):
        data = {'szwHostName': szwHostName, 'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.AcquireKeysForProductOnHost2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetKeyDataForHost(self, szwSerial, szwHostName, szwProduct, szwVersion):
        data = {'szwSerial': szwSerial, 'szwHostName': szwHostName, 'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'LicenseInfoSync.GetKeyDataForHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

