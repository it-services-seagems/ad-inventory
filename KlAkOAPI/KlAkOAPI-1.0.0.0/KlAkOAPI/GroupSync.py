#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkGroupSync (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetSyncInfo(self, nSync, arrFieldsToReturn):
        data = {'nSync': nSync, 'arrFieldsToReturn': arrFieldsToReturn}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupSync.GetSyncInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSyncHostsInfo(self, nSync, arrFieldsToReturn, arrFieldsToOrder, nLifeTime):
        data = {'nSync': nSync, 'arrFieldsToReturn': arrFieldsToReturn, 'arrFieldsToOrder': arrFieldsToOrder, 'nLifeTime': nLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupSync.GetSyncHostsInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSyncDeliveryTime(self, nSync, szwHostId):
        data = {'nSync': nSync, 'szwHostId': szwHostId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupSync.GetSyncDeliveryTime'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

