#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkKeyService (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def DecryptData(self, pEncryptedData, wstrProdName, wstrProdVersion):
        data = {'pEncryptedData': pEncryptedData, 'wstrProdName': wstrProdName, 'wstrProdVersion': wstrProdVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KeyService.DecryptData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pDecryptedData'])

    def EncryptDataForHost(self, wstrHostId, pData):
        data = {'wstrHostId': wstrHostId, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KeyService.EncryptDataForHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEncryptedData'])

    def EncryptData(self, pData):
        data = {'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KeyService.EncryptData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEncryptedData'])

    def GenerateTransportCertificate(self, wstrCommonName):
        data = {'wstrCommonName': wstrCommonName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KeyService.GenerateTransportCertificate'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pPublic', 'pPrivate', 'wstrPass'])

