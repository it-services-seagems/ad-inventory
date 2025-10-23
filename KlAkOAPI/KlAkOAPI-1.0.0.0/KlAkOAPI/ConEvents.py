#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkConEvents (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def Subscribe(self, wstrEvent, pFilter):
        data = {'wstrEvent': wstrEvent, 'pFilter': pFilter}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ConEvents.Subscribe'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['nPeriod'])

    def UnSubscribe(self, nSubsId):
        data = {'nSubsId': nSubsId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ConEvents.UnSubscribe'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def Retrieve(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ConEvents.Retrieve'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['pEvents', 'nPeriod'])

    def IsServiceConsoleAvailable(self, wstrProdName, wstrProdVersion):
        data = {'wstrProdName': wstrProdName, 'wstrProdVersion': wstrProdVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ConEvents.IsServiceConsoleAvailable'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def IsAnyServiceConsoleAvailable(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ConEvents.IsAnyServiceConsoleAvailable'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

