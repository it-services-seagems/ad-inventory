#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkAdHosts (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetChildComputers(self, idOU, vecFieldsToReturn, lMaxLifeTime):
        data = {'idOU': idOU, 'vecFieldsToReturn': vecFieldsToReturn, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'AdHosts.GetChildComputers'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetChildOUs(self, idOU, pFields, lMaxLifeTime):
        data = {'idOU': idOU, 'pFields': pFields, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'AdHosts.GetChildOUs'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetOU(self, idOU, pFields):
        data = {'idOU': idOU, 'pFields': pFields}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'AdHosts.GetOU'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateOU(self, idOU, pData):
        data = {'idOU': idOU, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'AdHosts.UpdateOU'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def FindAdGroups(self, vecFieldsToReturn, vecFieldsToOrder, pOptions, lMaxLifeTime):
        data = {'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'pOptions': pOptions, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'AdHosts.FindAdGroups'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['wstrIterator'])

    def GetChildComputer(self, idAdhst, vecFieldsToReturn):
        data = {'idAdhst': idAdhst, 'vecFieldsToReturn': vecFieldsToReturn}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'AdHosts.GetChildComputer'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

