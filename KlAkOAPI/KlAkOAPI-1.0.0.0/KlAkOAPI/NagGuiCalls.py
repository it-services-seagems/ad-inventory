#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkNagGuiCalls (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def CallConnectorAsync(self, szwProduct, szwVersion, szwCallName, pInData):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion, 'szwCallName': szwCallName, 'pInData': pInData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagGuiCalls.CallConnectorAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

