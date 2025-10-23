#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkNagRemoteScreen (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetExistingSessions(self, nType):
        data = {'nType': nType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRemoteScreen.GetExistingSessions'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def OpenSession(self, nType, szwID):
        data = {'nType': nType, 'szwID': szwID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRemoteScreen.OpenSession'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CloseSession(self, pSharingHandle):
        data = {'pSharingHandle': pSharingHandle}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRemoteScreen.CloseSession'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetDataForTunnel(self, pSharingHandle):
        data = {'pSharingHandle': pSharingHandle}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRemoteScreen.GetDataForTunnel'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['nHostPortNumber', 'wstrHostNameOrIpAddr'])

    def GetWdsData(self, pSharingHandle, nLocalPortNumber):
        data = {'pSharingHandle': pSharingHandle, 'nLocalPortNumber': nLocalPortNumber}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRemoteScreen.GetWdsData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrTicket', 'wstrPassword'])

