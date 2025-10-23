#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkPluginData (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def StorePluginData(self, wstrPluginName, pData):
        data = {'wstrPluginName': wstrPluginName, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginData.StorePluginData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def LoadPluginData(self, wstrPluginName):
        data = {'wstrPluginName': wstrPluginName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginData.LoadPluginData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

