#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkGatewayConnection (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def PrepareGatewayConnection(self, pLocations):
        data = {'pLocations': pLocations}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GatewayConnection.PrepareGatewayConnection'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAuthKey'])

    def PrepareTunnelConnection(self, pLocations, szwTargetHostName, nTargetPort):
        data = {'pLocations': pLocations, 'szwTargetHostName': szwTargetHostName, 'nTargetPort': nTargetPort}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GatewayConnection.PrepareTunnelConnection'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAuthKey'])

    def TestOapiTunnelMethod(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GatewayConnection.TestOapiTunnelMethod'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

