#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkEventProcessingFactory (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def CreateEventProcessing(self, vecFieldsToReturn, vecFieldsToOrder, lifetimeSec):
        data = {'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'lifetimeSec': lifetimeSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'EventProcessingFactory.CreateEventProcessing'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strIteratorId'])

    def CreateEventProcessing2(self, pFilter, vecFieldsToReturn, vecFieldsToOrder, lifetimeSec):
        data = {'pFilter': pFilter, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'lifetimeSec': lifetimeSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'EventProcessingFactory.CreateEventProcessing2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strIteratorId'])

    def CreateEventProcessingForHost(self, strHostName, strProduct, strVersion, vecFieldsToReturn, vecFieldsToOrder, lifetimeSec):
        data = {'strHostName': strHostName, 'strProduct': strProduct, 'strVersion': strVersion, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'lifetimeSec': lifetimeSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'EventProcessingFactory.CreateEventProcessingForHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strIteratorId'])

    def CreateEventProcessingForHost2(self, strHostName, strProduct, strVersion, pFilter, vecFieldsToReturn, vecFieldsToOrder, lifetimeSec):
        data = {'strHostName': strHostName, 'strProduct': strProduct, 'strVersion': strVersion, 'pFilter': pFilter, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'lifetimeSec': lifetimeSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'EventProcessingFactory.CreateEventProcessingForHost2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strIteratorId'])

