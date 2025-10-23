#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkTasks (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetTask(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RunTask(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.RunTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SuspendTask(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.SuspendTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ResumeTask(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ResumeTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CancelTask(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.CancelTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetTaskStatistics(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetTaskStatistics'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetTaskHistory(self, strTask, pFields2Return, pSortFields, strHostName, pFilter):
        data = {'strTask': strTask, 'pFields2Return': pFields2Return, 'pSortFields': pSortFields, 'strHostName': strHostName, 'pFilter': pFilter}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetTaskHistory'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strIteratorId'])

    def DeleteTask(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.DeleteTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetTaskData(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetTaskData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddTask(self, pData):
        data = {'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.AddTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateTask(self, strTask, pData):
        data = {'strTask': strTask, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.UpdateTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ProtectPassword(self, strPassword):
        data = {'strPassword': strPassword}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ProtectPassword'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetTaskStartEvent(self, strTask, pData):
        data = {'strTask': strTask, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.SetTaskStartEvent'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetTaskStartEvent(self, strTask):
        data = {'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetTaskStartEvent'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ResetHostIteratorForTaskStatus(self, strTask, pFields2Return, nHostStateMask, nLifetime):
        data = {'strTask': strTask, 'pFields2Return': pFields2Return, 'nHostStateMask': nHostStateMask, 'nLifetime': nLifetime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ResetHostIteratorForTaskStatus'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strHostIteratorId'])

    def GetNextHostStatus(self, strHostIteratorId, nCount):
        data = {'strHostIteratorId': strHostIteratorId, 'nCount': nCount}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetNextHostStatus'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['nActual', 'pHostStatus'])

    def ResetHostIteratorForTaskStatusEx(self, strTask, pFields2Return, pFields2Order, nHostStateMask, nLifetime):
        data = {'strTask': strTask, 'pFields2Return': pFields2Return, 'pFields2Order': pFields2Order, 'nHostStateMask': nHostStateMask, 'nLifetime': nLifetime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ResetHostIteratorForTaskStatusEx'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strHostIteratorId'])

    def GetHostStatusRecordsCount(self, strHostIteratorId):
        data = {'strHostIteratorId': strHostIteratorId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetHostStatusRecordsCount'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetHostStatusRecordRange(self, strHostIteratorId, nStart, nEnd):
        data = {'strHostIteratorId': strHostIteratorId, 'nStart': nStart, 'nEnd': nEnd}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetHostStatusRecordRange'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['pParHostStatus'])

    def ReleaseHostStatusIterator(self, strHostIteratorId):
        data = {'strHostIteratorId': strHostIteratorId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ReleaseHostStatusIterator'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetAllTasksOfHost(self, strDomainName, strHostName):
        data = {'strDomainName': strDomainName, 'strHostName': strHostName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetAllTasksOfHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetTaskGroup(self, strTaskId):
        data = {'strTaskId': strTaskId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetTaskGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ResolveTaskId(self, strPrtsTaskId):
        data = {'strPrtsTaskId': strPrtsTaskId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ResolveTaskId'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ResetTasksIterator(self, nGroupId, bGroupIdSignificant, strProductName, strVersion, strComponentName, strInstanceId, strTaskName, bIncludeSupergroups):
        data = {'nGroupId': nGroupId, 'bGroupIdSignificant': bGroupIdSignificant, 'strProductName': strProductName, 'strVersion': strVersion, 'strComponentName': strComponentName, 'strInstanceId': strInstanceId, 'strTaskName': strTaskName, 'bIncludeSupergroups': bIncludeSupergroups}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ResetTasksIterator'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['strTaskIteratorId'])

    def GetNextTask(self, strTaskIteratorId):
        data = {'strTaskIteratorId': strTaskIteratorId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.GetNextTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pTaskData'])

    def ReleaseTasksIterator(self, strTaskIteratorId):
        data = {'strTaskIteratorId': strTaskIteratorId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.ReleaseTasksIterator'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def UpdateCredPasswords(self, wstrUser, wstrPass, wstrOldPass, pActions):
        data = {'wstrUser': wstrUser, 'wstrPass': wstrPass, 'wstrOldPass': wstrOldPass, 'pActions': pActions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.UpdateCredPasswords'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateCredPasswordsAsync(self, wstrUser, wstrPass, wstrOldPass, pActions, wstrRequestId):
        data = {'wstrUser': wstrUser, 'wstrPass': wstrPass, 'wstrOldPass': wstrOldPass, 'pActions': pActions, 'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.UpdateCredPasswordsAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CancelUpdateCredPasswords(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'Tasks.CancelUpdateCredPasswords'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

