#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkHostTasks (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def ResetTasksIterator(self, strSrvObjId, strProductName, strVersion, strComponentName, strInstanceId, strTaskName):
        data = {'strSrvObjId': strSrvObjId, 'strProductName': strProductName, 'strVersion': strVersion, 'strComponentName': strComponentName, 'strInstanceId': strInstanceId, 'strTaskName': strTaskName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.ResetTasksIterator'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetNextTask(self, strSrvObjId):
        data = {'strSrvObjId': strSrvObjId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.GetNextTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pTaskData'])

    def GetTaskData(self, strSrvObjId, strTask):
        data = {'strSrvObjId': strSrvObjId, 'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.GetTaskData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddTask(self, strSrvObjId, pData):
        data = {'strSrvObjId': strSrvObjId, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.AddTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateTask(self, strSrvObjId, strTask, pData):
        data = {'strSrvObjId': strSrvObjId, 'strTask': strTask, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.UpdateTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteTask(self, strSrvObjId, strTask):
        data = {'strSrvObjId': strSrvObjId, 'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.DeleteTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SetTaskStartEvent(self, strSrvObjId, strTask, pData):
        data = {'strSrvObjId': strSrvObjId, 'strTask': strTask, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.SetTaskStartEvent'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetTaskStartEvent(self, strSrvObjId, strTask):
        data = {'strSrvObjId': strSrvObjId, 'strTask': strTask}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HostTasks.GetTaskStartEvent'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

