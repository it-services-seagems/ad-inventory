#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkPolicyProfiles (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def EnumProfiles(self, nPolicy, nRevision):
        data = {'nPolicy': nPolicy, 'nRevision': nRevision}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.EnumProfiles'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetProfile(self, nPolicy, nRevision, szwName):
        data = {'nPolicy': nPolicy, 'nRevision': nRevision, 'szwName': szwName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.GetProfile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddProfile(self, nPolicy, szwName, pAttrs, nLifeTime):
        data = {'nPolicy': nPolicy, 'szwName': szwName, 'pAttrs': pAttrs, 'nLifeTime': nLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.AddProfile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateProfile(self, nPolicy, szwName, pAttrsToUpdate):
        data = {'nPolicy': nPolicy, 'szwName': szwName, 'pAttrsToUpdate': pAttrsToUpdate}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.UpdateProfile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def RenameProfile(self, nPolicy, szwExistingName, szwNewName):
        data = {'nPolicy': nPolicy, 'szwExistingName': szwExistingName, 'szwNewName': szwNewName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.RenameProfile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteProfile(self, nPolicy, szwName):
        data = {'nPolicy': nPolicy, 'szwName': szwName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.DeleteProfile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetProfileSettings(self, nPolicy, nRevision, szwName, nLifeTime):
        data = {'nPolicy': nPolicy, 'nRevision': nRevision, 'szwName': szwName, 'nLifeTime': nLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.GetProfileSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetPriorities(self, nPolicy, nRevision):
        data = {'nPolicy': nPolicy, 'nRevision': nRevision}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.GetPriorities'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def PutPriorities(self, nPolicy, pArrayOfNames):
        data = {'nPolicy': nPolicy, 'pArrayOfNames': pArrayOfNames}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.PutPriorities'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetEffectivePolicyContents(self, nPolicy, szwHostId, nLifeTime):
        data = {'nPolicy': nPolicy, 'szwHostId': szwHostId, 'nLifeTime': nLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.GetEffectivePolicyContents'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ExportProfile(self, lPolicy, szwName):
        data = {'lPolicy': lPolicy, 'szwName': szwName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.ExportProfile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ImportProfile(self, lPolicy, pData):
        data = {'lPolicy': lPolicy, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PolicyProfiles.ImportProfile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

