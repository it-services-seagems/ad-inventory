#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkGroupSyncIterator (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetNextItems(self, szwIterator, nCount):
        data = {'szwIterator': szwIterator, 'nCount': nCount}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupSyncIterator.GetNextItems'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['bEOF', 'pData'])

    def ReleaseIterator(self, szwIterator):
        data = {'szwIterator': szwIterator}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupSyncIterator.ReleaseIterator'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

