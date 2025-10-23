#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkKLEVerTestApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def UpdateKSCData(self, wstrKSCFolder):
        data = {'wstrKSCFolder': wstrKSCFolder}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerTestApi.UpdateKSCData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ResetModificationTime(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerTestApi.ResetModificationTime'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetTestListenerPort(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerTestApi.GetTestListenerPort'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CheckNewDistributivesAvailable(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerTestApi.CheckNewDistributivesAvailable'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CheckNewKleverDistributives(self, parLastViewedTimes):
        data = {'parLastViewedTimes': parLastViewedTimes}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KLEVerTestApi.CheckNewKleverDistributives'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

