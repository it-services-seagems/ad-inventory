#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkPluginDataStorage (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def EnumAllKeys(self, wstrPluginName):
        data = {'wstrPluginName': wstrPluginName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginDataStorage.EnumAllKeys'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def LoadValues(self, wstrPluginName, pArrayOfKeys):
        data = {'wstrPluginName': wstrPluginName, 'pArrayOfKeys': pArrayOfKeys}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginDataStorage.LoadValues'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteValue(self, wstrPluginName, wstrKey):
        data = {'wstrPluginName': wstrPluginName, 'wstrKey': wstrKey}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginDataStorage.DeleteValue'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ReplaceValues(self, wstrPluginName, pValues):
        data = {'wstrPluginName': wstrPluginName, 'pValues': pValues}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginDataStorage.ReplaceValues'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def StartUploadValue(self, wstrPluginName, nValueSize):
        data = {'wstrPluginName': wstrPluginName, 'nValueSize': nValueSize}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginDataStorage.StartUploadValue'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def FinishUploadValue(self, wstrUrl, wstrKey):
        data = {'wstrUrl': wstrUrl, 'wstrKey': wstrKey}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PluginDataStorage.FinishUploadValue'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

