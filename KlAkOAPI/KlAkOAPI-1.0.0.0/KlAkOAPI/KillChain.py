#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkKillChain (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetByIDs(self, wstrHostID, wstrElementID):
        data = {'wstrHostID': wstrHostID, 'wstrElementID': wstrElementID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KillChain.GetByIDs'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['nResStatus'])

    def GetByIDs2(self, wstrHostID, wstrProductName, wstrProductVersion, wstrElementID):
        data = {'wstrHostID': wstrHostID, 'wstrProductName': wstrProductName, 'wstrProductVersion': wstrProductVersion, 'wstrElementID': wstrElementID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KillChain.GetByIDs2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['nResStatus'])

