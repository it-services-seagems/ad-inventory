#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkSrvView (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def ResetIterator(self, wstrViewName, wstrFilter, vecFieldsToReturn, vecFieldsToOrder, pParams, lifetimeSec):
        data = {'wstrViewName': wstrViewName, 'wstrFilter': wstrFilter, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'pParams': pParams, 'lifetimeSec': lifetimeSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SrvView.ResetIterator'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrIteratorId'])

    def GetRecordCount(self, wstrIteratorId):
        data = {'wstrIteratorId': wstrIteratorId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SrvView.GetRecordCount'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetRecordRange(self, wstrIteratorId, nStart, nEnd):
        data = {'wstrIteratorId': wstrIteratorId, 'nStart': nStart, 'nEnd': nEnd}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SrvView.GetRecordRange'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pRecords'])

    def ReleaseIterator(self, wstrIteratorId):
        data = {'wstrIteratorId': wstrIteratorId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SrvView.ReleaseIterator'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ResetIteratorAsync(self, wstrViewName, wstrFilter, vecFieldsToReturn, vecFieldsToOrder, pParams, lifetimeSec):
        data = {'wstrViewName': wstrViewName, 'wstrFilter': wstrFilter, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'pParams': pParams, 'lifetimeSec': lifetimeSec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SrvView.ResetIteratorAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ResetIteratorAsyncGetData(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SrvView.ResetIteratorAsyncGetData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ResetIteratorAsyncCancel(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SrvView.ResetIteratorAsyncCancel'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

