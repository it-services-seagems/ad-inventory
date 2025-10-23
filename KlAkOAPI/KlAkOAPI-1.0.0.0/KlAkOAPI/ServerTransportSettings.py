#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkServerTransportSettings (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def IsFeatureActive(self, szwCertType):
        data = {'szwCertType': szwCertType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.IsFeatureActive'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetFeatureActive(self, szwCertType, bFeatureActive):
        data = {'szwCertType': szwCertType, 'bFeatureActive': bFeatureActive}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.SetFeatureActive'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetCustomSrvCertificateInfo(self, szwCertType):
        data = {'szwCertType': szwCertType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.GetCustomSrvCertificateInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetCustomSrvCertificate(self, szwCertType, pCertData):
        data = {'szwCertType': szwCertType, 'pCertData': pCertData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.SetCustomSrvCertificate'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CheckDefaultCertificateExists(self, szwCertType):
        data = {'szwCertType': szwCertType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.CheckDefaultCertificateExists'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetOrCreateDefaultCertificate(self, szwCertType, pSettings):
        data = {'szwCertType': szwCertType, 'pSettings': pSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.SetOrCreateDefaultCertificate'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetDefaultConnectionSettings(self, szwCertType):
        data = {'szwCertType': szwCertType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.GetDefaultConnectionSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetCurrentConnectionSettings(self, szwCertType):
        data = {'szwCertType': szwCertType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.GetCurrentConnectionSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ResetDefaultReserveCertificate(self, szwCertType):
        data = {'szwCertType': szwCertType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.ResetDefaultReserveCertificate'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ResetCstmReserveCertificate(self, szwCertType):
        data = {'szwCertType': szwCertType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.ResetCstmReserveCertificate'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetNumberOfManagedDevicesKSM(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.GetNumberOfManagedDevicesKSM'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetNumberOfManagedDevicesAgentless(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ServerTransportSettings.GetNumberOfManagedDevicesAgentless'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

