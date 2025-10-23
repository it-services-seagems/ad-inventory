#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkServiceNwcDeployment (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def CreateServiceAccount(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServiceNwcDeployment.CreateServiceAccount'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pAccount'])

    def UpdateServiceAccountAcl(self, pAclParams):
        data = {'pAclParams': pAclParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServiceNwcDeployment.UpdateServiceAccountAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

