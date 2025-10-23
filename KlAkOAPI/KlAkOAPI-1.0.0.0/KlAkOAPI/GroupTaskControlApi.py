#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkGroupTaskControlApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def ResetTasksIteratorForCluster(self, szwClusterId, szwProductName, szwVersion, szwComponentName, szwInstanceId, szwTaskName):
        data = {'szwClusterId': szwClusterId, 'szwProductName': szwProductName, 'szwVersion': szwVersion, 'szwComponentName': szwComponentName, 'szwInstanceId': szwInstanceId, 'szwTaskName': szwTaskName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupTaskControlApi.ResetTasksIteratorForCluster'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RequestStatistics(self, pTasksIds):
        data = {'pTasksIds': pTasksIds}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupTaskControlApi.RequestStatistics'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetTaskByRevision(self, nObjId, nRevision):
        data = {'nObjId': nObjId, 'nRevision': nRevision}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupTaskControlApi.GetTaskByRevision'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RestoreTaskFromRevision(self, nObjId, nRevision):
        data = {'nObjId': nObjId, 'nRevision': nRevision}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupTaskControlApi.RestoreTaskFromRevision'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ExportTask(self, wstrTaskId):
        data = {'wstrTaskId': wstrTaskId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupTaskControlApi.ExportTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ImportTask(self, pBlob, pExtraData):
        data = {'pBlob': pBlob, 'pExtraData': pExtraData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupTaskControlApi.ImportTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['pCommitInfo'])

    def CommitImportedTask(self, wstrId, bCommit):
        data = {'wstrId': wstrId, 'bCommit': bCommit}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'GroupTaskControlApi.CommitImportedTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

