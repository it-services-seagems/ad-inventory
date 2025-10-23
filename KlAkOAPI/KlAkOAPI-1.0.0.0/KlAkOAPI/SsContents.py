#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkSsContents (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def Ss_Read(self, wstrID, wstrProduct, wstrVersion, wstrSection):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Read'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SS_GetNames(self, wstrID, wstrProduct, wstrVersion):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.SS_GetNames'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def Ss_Update(self, wstrID, wstrProduct, wstrVersion, wstrSection, pNewData):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'pNewData': pNewData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Update'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_Add(self, wstrID, wstrProduct, wstrVersion, wstrSection, pNewData):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'pNewData': pNewData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Add'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_Replace(self, wstrID, wstrProduct, wstrVersion, wstrSection, pNewData):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'pNewData': pNewData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Replace'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_Clear(self, wstrID, wstrProduct, wstrVersion, wstrSection, pNewData):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'pNewData': pNewData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Clear'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_Delete(self, wstrID, wstrProduct, wstrVersion, wstrSection, pData):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Delete'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_CreateSection(self, wstrID, wstrProduct, wstrVersion, wstrSection):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_CreateSection'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_DeleteSection(self, wstrID, wstrProduct, wstrVersion, wstrSection):
        data = {'wstrID': wstrID, 'wstrProduct': wstrProduct, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_DeleteSection'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_Apply(self, wstrID):
        data = {'wstrID': wstrID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Apply'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Ss_Release(self, wstrID):
        data = {'wstrID': wstrID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SsContents.Ss_Release'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

