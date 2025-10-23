#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkHostGroup (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def AddHost(self, pInfo):
        data = {'pInfo': pInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.AddHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateHost(self, strHostName, pInfo):
        data = {'strHostName': strHostName, 'pInfo': pInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.UpdateHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def UpdateHostsMultiple(self, pArrHostIds, pProperties):
        data = {'pArrHostIds': pArrHostIds, 'pProperties': pProperties}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.UpdateHostsMultiple'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RemoveHost(self, strHostName):
        data = {'strHostName': strHostName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.RemoveHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetHostInfo(self, strHostName, pFields2Return):
        data = {'strHostName': strHostName, 'pFields2Return': pFields2Return}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetHostInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def FindHosts(self, wstrFilter, vecFieldsToReturn, vecFieldsToOrder, pParams, lMaxLifeTime):
        data = {'wstrFilter': wstrFilter, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'pParams': pParams, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.FindHosts'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['strAccessor'])

    def MoveHostsToGroup(self, nGroup, pHostNames):
        data = {'nGroup': nGroup, 'pHostNames': pHostNames}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.MoveHostsToGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def MoveHostsFromGroupToGroup(self, nSrcGroupId, nDstGroupId):
        data = {'nSrcGroupId': nSrcGroupId, 'nDstGroupId': nDstGroupId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.MoveHostsFromGroupToGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strActionGuid'])

    def RemoveHosts(self, pHostNames, bForceDestroy):
        data = {'pHostNames': pHostNames, 'bForceDestroy': bForceDestroy}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.RemoveHosts'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ZeroVirusCountForGroup(self, nParent):
        data = {'nParent': nParent}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.ZeroVirusCountForGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strActionGuid'])

    def ZeroVirusCountForHosts(self, pHostNames):
        data = {'pHostNames': pHostNames}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.ZeroVirusCountForHosts'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strActionGuid'])

    def AddHostsForSync(self, pHostNames, strSSType):
        data = {'pHostNames': pHostNames, 'strSSType': strSSType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.AddHostsForSync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strActionGuid'])

    def AddGroupHostsForSync(self, nGroupId, strSSType):
        data = {'nGroupId': nGroupId, 'strSSType': strSSType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.AddGroupHostsForSync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strActionGuid'])

    def GroupIdGroups(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GroupIdGroups'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GroupIdUnassigned(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GroupIdUnassigned'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GroupIdSuper(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GroupIdSuper'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddGroup(self, pInfo):
        data = {'pInfo': pInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.AddGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateGroup(self, nGroup, pInfo):
        data = {'nGroup': nGroup, 'pInfo': pInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.UpdateGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def RemoveGroup(self, nGroup, nFlags):
        data = {'nGroup': nGroup, 'nFlags': nFlags}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.RemoveGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strActionGuid'])

    def GetGroupInfo(self, nGroupId):
        data = {'nGroupId': nGroupId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetGroupInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetGroupInfoEx(self, nGroupId, pArrAttributes):
        data = {'nGroupId': nGroupId, 'pArrAttributes': pArrAttributes}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetGroupInfoEx'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSubgroups(self, nGroupId, nDepth):
        data = {'nGroupId': nGroupId, 'nDepth': nDepth}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetSubgroups'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetGroupId(self, nParent, strName):
        data = {'nParent': nParent, 'strName': strName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetGroupId'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def FindGroups(self, wstrFilter, vecFieldsToReturn, vecFieldsToOrder, pParams, lMaxLifeTime):
        data = {'wstrFilter': wstrFilter, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'pParams': pParams, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.FindGroups'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['strAccessor'])

    def ResolveAndMoveToGroup(self, pInfo):
        data = {'pInfo': pInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.ResolveAndMoveToGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pResults'])

    def GetDomains(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetDomains'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetDomainHosts(self, domain):
        data = {'domain': domain}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetDomainHosts'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddDomain(self, strDomain, nType):
        data = {'strDomain': strDomain, 'nType': nType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.AddDomain'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DelDomain(self, strDomain):
        data = {'strDomain': strDomain}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.DelDomain'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetHostProducts(self, strHostName):
        data = {'strHostName': strHostName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetHostProducts'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SS_Read(self, strHostName, strType, strProduct, strVersion, strSection):
        data = {'strHostName': strHostName, 'strType': strType, 'strProduct': strProduct, 'strVersion': strVersion, 'strSection': strSection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.SS_Read'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SS_Write(self, strHostName, strType, strProduct, strVersion, strSection, nOption, pSettings):
        data = {'strHostName': strHostName, 'strType': strType, 'strProduct': strProduct, 'strVersion': strVersion, 'strSection': strSection, 'nOption': nOption, 'pSettings': pSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.SS_Write'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SS_CreateSection(self, strHostName, strType, strProduct, strVersion, strSection):
        data = {'strHostName': strHostName, 'strType': strType, 'strProduct': strProduct, 'strVersion': strVersion, 'strSection': strSection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.SS_CreateSection'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SS_DeleteSection(self, strHostName, strType, strProduct, strVersion, strSection):
        data = {'strHostName': strHostName, 'strType': strType, 'strProduct': strProduct, 'strVersion': strVersion, 'strSection': strSection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.SS_DeleteSection'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SS_GetNames(self, strHostName, strType, strProduct, strVersion):
        data = {'strHostName': strHostName, 'strType': strType, 'strProduct': strProduct, 'strVersion': strVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.SS_GetNames'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetRunTimeInfo(self, pValues):
        data = {'pValues': pValues}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetRunTimeInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetStaticInfo(self, pValues):
        data = {'pValues': pValues}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetStaticInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RestartNetworkScanning(self, nType):
        data = {'nType': nType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.RestartNetworkScanning'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetHostfixesForProductOnHost(self, strHostName, strProductName, strProductVersion):
        data = {'strHostName': strHostName, 'strProductName': strProductName, 'strProductVersion': strProductVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetHostfixesForProductOnHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetAllHostfixes(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetAllHostfixes'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def FindIncidents(self, strFilter, pFieldsToReturn, pFieldsToOrder, lMaxLifeTime):
        data = {'strFilter': strFilter, 'pFieldsToReturn': pFieldsToReturn, 'pFieldsToOrder': pFieldsToOrder, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.FindIncidents'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['strAccessor'])

    def AddIncident(self, pData):
        data = {'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.AddIncident'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateIncident(self, nId, pData):
        data = {'nId': nId, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.UpdateIncident'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteIncident(self, nId):
        data = {'nId': nId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.DeleteIncident'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def FindUsers(self, strFilter, pFieldsToReturn, pFieldsToOrder, lMaxLifeTime):
        data = {'strFilter': strFilter, 'pFieldsToReturn': pFieldsToReturn, 'pFieldsToOrder': pFieldsToOrder, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.FindUsers'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['strAccessor'])

    def SetLocInfo(self, pData):
        data = {'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.SetLocInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetHostTasks(self, strHostName):
        data = {'strHostName': strHostName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetHostTasks'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def FindHostsAsync(self, wstrFilter, vecFieldsToReturn, vecFieldsToOrder, pParams, lMaxLifeTime):
        data = {'wstrFilter': wstrFilter, 'vecFieldsToReturn': vecFieldsToReturn, 'vecFieldsToOrder': vecFieldsToOrder, 'pParams': pParams, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.FindHostsAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strRequestId'])

    def FindHostsAsyncCancel(self, strRequestId):
        data = {'strRequestId': strRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.FindHostsAsyncCancel'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def FindHostsAsyncGetAccessor(self, strRequestId):
        data = {'strRequestId': strRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.FindHostsAsyncGetAccessor'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['strAccessor', 'pFailedSlavesInfo'])

    def GetComponentsForProductOnHost(self, strHostName, strProductName, strProductVersion):
        data = {'strHostName': strHostName, 'strProductName': strProductName, 'strProductVersion': strProductVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetComponentsForProductOnHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetInstanceStatistics(self, vecFilterFields):
        data = {'vecFilterFields': vecFilterFields}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostGroup.GetInstanceStatistics'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

