#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkDatabaseInfo (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetDBSize(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.GetDBSize'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetDBDataSize(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.GetDBDataSize'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetDBEventsCount(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.GetDBEventsCount'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CheckBackupPath(self, szwPath):
        data = {'szwPath': szwPath}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.CheckBackupPath'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CheckBackupPath2(self, szwWinPath, szwLinuxPath):
        data = {'szwWinPath': szwWinPath, 'szwLinuxPath': szwLinuxPath}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.CheckBackupPath2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CheckBackupCloudPath(self, nCloudType, szwCloudPath, szwClientId, pSecretChunk, szwStorageKey, szwAzureResName, szwAzureResGroup, szwAzureAppID):
        data = {'nCloudType': nCloudType, 'szwCloudPath': szwCloudPath, 'szwClientId': szwClientId, 'pSecretChunk': pSecretChunk, 'szwStorageKey': szwStorageKey, 'szwAzureResName': szwAzureResName, 'szwAzureResGroup': szwAzureResGroup, 'szwAzureAppID': szwAzureAppID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.CheckBackupCloudPath'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CheckBackupCloudPath2(self, nCloudType, szwCloudPath, szwClientId, pSecretChunk, pStorageKey, szwAzureResName, szwAzureResGroup, szwAzureAppID):
        data = {'nCloudType': nCloudType, 'szwCloudPath': szwCloudPath, 'szwClientId': szwClientId, 'pSecretChunk': pSecretChunk, 'pStorageKey': pStorageKey, 'szwAzureResName': szwAzureResName, 'szwAzureResGroup': szwAzureResGroup, 'szwAzureAppID': szwAzureAppID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.CheckBackupCloudPath2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def IsCloudSQL(self, nCloudType):
        data = {'nCloudType': nCloudType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.IsCloudSQL'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def IsLinuxSQL(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DatabaseInfo.IsLinuxSQL'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

