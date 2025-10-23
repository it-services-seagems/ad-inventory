#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkDataProtectionApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def ProtectDataForHost(self, szwHostId, pData):
        data = {'szwHostId': szwHostId, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DataProtectionApi.ProtectDataForHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pDataProtected'])

    def ProtectDataGlobally(self, pData):
        data = {'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DataProtectionApi.ProtectDataGlobally'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pDataProtected'])

    def CheckPasswordSplPpc(self, szwPassword):
        data = {'szwPassword': szwPassword}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DataProtectionApi.CheckPasswordSplPpc'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ProtectUtf8StringForHost(self, szwHostId, szwPlainText):
        data = {'szwHostId': szwHostId, 'szwPlainText': szwPlainText}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DataProtectionApi.ProtectUtf8StringForHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ProtectUtf8StringGlobally(self, szwPlainText):
        data = {'szwPlainText': szwPlainText}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DataProtectionApi.ProtectUtf8StringGlobally'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ProtectUtf16StringForHost(self, szwHostId, szwPlainText):
        data = {'szwHostId': szwHostId, 'szwPlainText': szwPlainText}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DataProtectionApi.ProtectUtf16StringForHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ProtectUtf16StringGlobally(self, szwPlainText):
        data = {'szwPlainText': szwPlainText}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DataProtectionApi.ProtectUtf16StringGlobally'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

