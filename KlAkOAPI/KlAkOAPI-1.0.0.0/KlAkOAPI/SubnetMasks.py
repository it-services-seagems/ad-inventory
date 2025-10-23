#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkSubnetMasks (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def CreateSubnet(self, pSubnetSettings):
        data = {'pSubnetSettings': pSubnetSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SubnetMasks.CreateSubnet'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ModifySubnet(self, nIpAddress, nMask, pSubnetSettings):
        data = {'nIpAddress': nIpAddress, 'nMask': nMask, 'pSubnetSettings': pSubnetSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SubnetMasks.ModifySubnet'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteSubnet(self, nIpAddress, nMask):
        data = {'nIpAddress': nIpAddress, 'nMask': nMask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SubnetMasks.DeleteSubnet'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

