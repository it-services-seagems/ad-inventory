#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkNlaDefinedNetworks (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def AddNetwork(self, wstrNetworkName):
        data = {'wstrNetworkName': wstrNetworkName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NlaDefinedNetworks.AddNetwork'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetNetworkInfo(self, pNetwork):
        data = {'pNetwork': pNetwork}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NlaDefinedNetworks.SetNetworkInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetNetworkInfo(self, nNetworkId):
        data = {'nNetworkId': nNetworkId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NlaDefinedNetworks.GetNetworkInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pNetwork'])

    def GetNetworksList(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NlaDefinedNetworks.GetNetworksList'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pNetworks'])

    def DeleteNetwork(self, nNetworkId):
        data = {'nNetworkId': nNetworkId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NlaDefinedNetworks.DeleteNetwork'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

