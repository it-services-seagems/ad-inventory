#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkKLEVerControl (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def ChangeCreatePackage(self, vecDistribLocIdsToCreate, vecDistribLocIdsNotToCreate, parParams):
        data = {'vecDistribLocIdsToCreate': vecDistribLocIdsToCreate, 'vecDistribLocIdsNotToCreate': vecDistribLocIdsNotToCreate, 'parParams': parParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerControl.ChangeCreatePackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DownloadDistributiveAsync(self, lDistribLocId, pExtendedSettings):
        data = {'lDistribLocId': lDistribLocId, 'pExtendedSettings': pExtendedSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerControl.DownloadDistributiveAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DownloadDistributiveAsyncInner(self, wstrRequestId, lDistribLocId, pExtendedSettings):
        data = {'wstrRequestId': wstrRequestId, 'lDistribLocId': lDistribLocId, 'pExtendedSettings': pExtendedSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerControl.DownloadDistributiveAsyncInner'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CancelDownloadDistributive(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerControl.CancelDownloadDistributive'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetDownloadDistributiveResult(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerControl.GetDownloadDistributiveResult'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrDownloadPath'])

