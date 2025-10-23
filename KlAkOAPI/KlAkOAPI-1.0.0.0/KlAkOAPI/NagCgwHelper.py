#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkNagCgwHelper (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetProductComponentLocation(self, szwProduct, szwVersion, szwComponent):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion, 'szwComponent': szwComponent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagCgwHelper.GetProductComponentLocation'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

