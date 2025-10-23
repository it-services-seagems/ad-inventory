#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkVapmControlApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetEulasIdsForPatchPrerequisites(self, llPatchGlobalId, nLCID):
        data = {'llPatchGlobalId': llPatchGlobalId, 'nLCID': nLCID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetEulasIdsForPatchPrerequisites'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEulasIds'])

    def GetSupportedLcidsForPatchPrerequisites(self, llPatchGlobalId, nOriginalLcid):
        data = {'llPatchGlobalId': llPatchGlobalId, 'nOriginalLcid': nOriginalLcid}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetSupportedLcidsForPatchPrerequisites'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pLcids'])

    def DownloadPatchAsync(self, llPatchGlbId, nLcid, wstrRequestId):
        data = {'llPatchGlbId': llPatchGlbId, 'nLcid': nLcid, 'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.DownloadPatchAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CancelDownloadPatch(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.CancelDownloadPatch'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetDownloadPatchResult(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetDownloadPatchResult'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrFileName', 'nSize'])

    def GetDownloadPatchDataChunk(self, wstrRequestId, nStartPos, nSizeMax):
        data = {'wstrRequestId': wstrRequestId, 'nStartPos': nStartPos, 'nSizeMax': nSizeMax}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetDownloadPatchDataChunk'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteFilesForUpdates(self, pUpdatesIds, wstrRequestId):
        data = {'pUpdatesIds': pUpdatesIds, 'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.DeleteFilesForUpdates'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteFilesForAllMicrosoftUpdates(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.DeleteFilesForAllMicrosoftUpdates'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteFilesForAll3rdPartyUpdates(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.DeleteFilesForAll3rdPartyUpdates'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteFilesForAllUpdates(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.DeleteFilesForAllUpdates'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CancelDeleteFilesForUpdates(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.CancelDeleteFilesForUpdates'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetAttributesSetVersionNum(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetAttributesSetVersionNum'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def InitiateDownload(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.InitiateDownload'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetUpdateSupportedLanguagesFilter(self, nUpdateSource):
        data = {'nUpdateSource': nUpdateSource}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetUpdateSupportedLanguagesFilter'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pSupportedLanguages'])

    def GetPendingRulesTasks(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetPendingRulesTasks'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pTasksIds'])

    def ChangeApproval(self, pUpdates, nApprovementState):
        data = {'pUpdates': pUpdates, 'nApprovementState': nApprovementState}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.ChangeApproval'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetEulasIdsForUpdates(self, pUpdates, nLcid):
        data = {'pUpdates': pUpdates, 'nLcid': nLcid}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetEulasIdsForUpdates'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEulaIds'])

    def GetEulaParams(self, nEulaId):
        data = {'nEulaId': nEulaId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetEulaParams'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEulaParams'])

    def GetEulasInfo(self, pUpdates, nLcid):
        data = {'pUpdates': pUpdates, 'nLcid': nLcid}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetEulasInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEulasInfo'])

    def AcceptEulas(self, pEulaIDs):
        data = {'pEulaIDs': pEulaIDs}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.AcceptEulas'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeclineEulas(self, pEulaIDs):
        data = {'pEulaIDs': pEulaIDs}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.DeclineEulas'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ChangeVulnerabilityIgnorance(self, wstrVulnerabilityUid, wstrHostId, bIgnore):
        data = {'wstrVulnerabilityUid': wstrVulnerabilityUid, 'wstrHostId': wstrHostId, 'bIgnore': bIgnore}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.ChangeVulnerabilityIgnorance'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SetPackagesToFixVulnerability(self, wstrVulnerabilityUid, pPackages, pParams):
        data = {'wstrVulnerabilityUid': wstrVulnerabilityUid, 'pPackages': pPackages, 'pParams': pParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.SetPackagesToFixVulnerability'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetEulasIdsForVulnerabilitiesPatches(self, pVulnerabilities, nLCID):
        data = {'pVulnerabilities': pVulnerabilities, 'nLCID': nLCID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'VapmControlApi.GetEulasIdsForVulnerabilitiesPatches'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

