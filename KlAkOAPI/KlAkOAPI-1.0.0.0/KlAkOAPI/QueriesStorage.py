#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkQueriesStorage (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetQueryIds(self, eType):
        data = {'eType': eType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QueriesStorage.GetQueryIds'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetQueries(self, eType):
        data = {'eType': eType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QueriesStorage.GetQueries'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetQuery(self, nId):
        data = {'nId': nId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QueriesStorage.GetQuery'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddQuery(self, eType, parData):
        data = {'eType': eType, 'parData': parData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QueriesStorage.AddQuery'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateQuery(self, nId, parData):
        data = {'nId': nId, 'parData': parData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QueriesStorage.UpdateQuery'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteQuery(self, nId):
        data = {'nId': nId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QueriesStorage.DeleteQuery'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

