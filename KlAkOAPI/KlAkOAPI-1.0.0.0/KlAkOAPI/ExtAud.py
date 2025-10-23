#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkExtAud (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetRevision(self, nObjId, nObjType, nObjRevision):
        data = {'nObjId': nObjId, 'nObjType': nObjType, 'nObjRevision': nObjRevision}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.GetRevision'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pObjParams'])

    def UpdateRevisionDesc(self, nObjId, nObjType, nObjRevision, wstrNewDescription):
        data = {'nObjId': nObjId, 'nObjType': nObjType, 'nObjRevision': nObjRevision, 'wstrNewDescription': wstrNewDescription}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.UpdateRevisionDesc'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def FinalDelete(self, arrObjects):
        data = {'arrObjects': arrObjects}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.FinalDelete'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SrvPutRevision(self, nObjId, nObjType, nOpCode, pObjParams, wstrSsPath, nUser, wstrUserDn, wstrObjName, wstrRevDesc):
        data = {'nObjId': nObjId, 'nObjType': nObjType, 'nOpCode': nOpCode, 'pObjParams': pObjParams, 'wstrSsPath': wstrSsPath, 'nUser': nUser, 'wstrUserDn': wstrUserDn, 'wstrObjName': wstrObjName, 'wstrRevDesc': wstrRevDesc}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.SrvPutRevision'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SrvGetRevision(self, nObjId, nObjType, nObjRevision, wstrSsPath):
        data = {'nObjId': nObjId, 'nObjType': nObjType, 'nObjRevision': nObjRevision, 'wstrSsPath': wstrSsPath}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.SrvGetRevision'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pObjParams'])

    def SrvDeleteOlder(self, tTime):
        data = {'tTime': tTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.SrvDeleteOlder'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SrvDeleteObjectRevisions(self, arrObjects):
        data = {'arrObjects': arrObjects}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.SrvDeleteObjectRevisions'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SrvUpdateRevisionDesc(self, nObjId, nObjType, nObjRevision, wstrNewDescription):
        data = {'nObjId': nObjId, 'nObjType': nObjType, 'nObjRevision': nObjRevision, 'wstrNewDescription': wstrNewDescription}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.SrvUpdateRevisionDesc'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SrvDoCleanerRoutine(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'ExtAud.SrvDoCleanerRoutine'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

