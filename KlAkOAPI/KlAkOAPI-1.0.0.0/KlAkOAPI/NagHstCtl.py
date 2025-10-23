#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkNagHstCtl (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetHostRuntimeInfo(self, pFilter):
        data = {'pFilter': pFilter}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagHstCtl.GetHostRuntimeInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SendProductAction(self, szwProduct, szwVersion, nProductAction):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion, 'nProductAction': nProductAction}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagHstCtl.SendProductAction'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SendTaskAction(self, szwProduct, szwVersion, szwTaskStorageId, nTaskAction):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion, 'szwTaskStorageId': szwTaskStorageId, 'nTaskAction': nTaskAction}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagHstCtl.SendTaskAction'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

