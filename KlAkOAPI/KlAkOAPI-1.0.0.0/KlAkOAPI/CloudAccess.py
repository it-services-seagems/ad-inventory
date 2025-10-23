#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkCloudAccess (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def AcquireAccessForKeyPair(self, enCloudType, pKeyPair):
        data = {'enCloudType': enCloudType, 'pKeyPair': pKeyPair}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'CloudAccess.AcquireAccessForKeyPair'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['bAllowScanning', 'bAllowDeployment'])

    def VerifyCredentials(self, enCloudType, pKeyPair):
        data = {'enCloudType': enCloudType, 'pKeyPair': pKeyPair}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'CloudAccess.VerifyCredentials'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

