#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkInvLicenseProducts (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetLicenseProducts(self, pParams):
        data = {'pParams': pParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'InvLicenseProducts.GetLicenseProducts'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddLicenseProduct(self, pLicProdData):
        data = {'pLicProdData': pLicProdData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'InvLicenseProducts.AddLicenseProduct'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateLicenseProduct(self, nLicProdId, pLicProdData):
        data = {'nLicProdId': nLicProdId, 'pLicProdData': pLicProdData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'InvLicenseProducts.UpdateLicenseProduct'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteLicenseProduct(self, nLicProdId):
        data = {'nLicProdId': nLicProdId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'InvLicenseProducts.DeleteLicenseProduct'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def AddLicenseKey(self, pLicKeyData):
        data = {'pLicKeyData': pLicKeyData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'InvLicenseProducts.AddLicenseKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateLicenseKey(self, nLicKeyId, pLicKeyData):
        data = {'nLicKeyId': nLicKeyId, 'pLicKeyData': pLicKeyData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'InvLicenseProducts.UpdateLicenseKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteLicenseKey(self, nLicKeyId):
        data = {'nLicKeyId': nLicKeyId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'InvLicenseProducts.DeleteLicenseKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

