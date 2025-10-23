#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkServerHierarchy (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetChildServers(self, nGroupId):
        data = {'nGroupId': nGroupId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerHierarchy.GetChildServers'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetServerInfo(self, lServer, pFields):
        data = {'lServer': lServer, 'pFields': pFields}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerHierarchy.GetServerInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RegisterServer(self, wstrDisplName, nGroupId, pCertificate, wstrNetAddress, pAdditionalInfo):
        data = {'wstrDisplName': wstrDisplName, 'nGroupId': nGroupId, 'pCertificate': pCertificate, 'wstrNetAddress': wstrNetAddress, 'pAdditionalInfo': pAdditionalInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerHierarchy.RegisterServer'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DelServer(self, lServer):
        data = {'lServer': lServer}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerHierarchy.DelServer'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def UpdateServer(self, lServer, pInfo):
        data = {'lServer': lServer, 'pInfo': pInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerHierarchy.UpdateServer'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def FindSlaveServers(self, wstrFilter, pFieldsToReturn, pFieldsToOrder, pParams, lMaxLifeTime):
        data = {'wstrFilter': wstrFilter, 'pFieldsToReturn': pFieldsToReturn, 'pFieldsToOrder': pFieldsToOrder, 'pParams': pParams, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerHierarchy.FindSlaveServers'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['wstrIterator'])

