#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkNagRdu (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetCurrentHostState(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.GetCurrentHostState'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ChangeTraceParams(self, szwProductID, nTraceLevel):
        data = {'szwProductID': szwProductID, 'nTraceLevel': nTraceLevel}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.ChangeTraceParams'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ChangeTraceRotatedParams(self, szwProductID, nTraceLevel, nPartsCount, nMaxPartSize):
        data = {'szwProductID': szwProductID, 'nTraceLevel': nTraceLevel, 'nPartsCount': nPartsCount, 'nMaxPartSize': nMaxPartSize}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.ChangeTraceRotatedParams'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ChangeXperfBaseParams(self, szwProductID, nTraceLevel, nXPerfMode):
        data = {'szwProductID': szwProductID, 'nTraceLevel': nTraceLevel, 'nXPerfMode': nXPerfMode}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.ChangeXperfBaseParams'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ChangeXperfRotatedParams(self, szwProductID, nTraceLevel, nXPerfMode, nMaxPartSize):
        data = {'szwProductID': szwProductID, 'nTraceLevel': nTraceLevel, 'nXPerfMode': nXPerfMode, 'nMaxPartSize': nMaxPartSize}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.ChangeXperfRotatedParams'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteFile(self, szwRemoteFile):
        data = {'szwRemoteFile': szwRemoteFile}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.DeleteFile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteFiles(self, pRemoteFiles):
        data = {'pRemoteFiles': pRemoteFiles}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.DeleteFiles'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetUrlToDownloadFileFromHost(self, szwRemoteFile):
        data = {'szwRemoteFile': szwRemoteFile}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.GetUrlToDownloadFileFromHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetUrlToUploadFileToHost(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.GetUrlToUploadFileToHost'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetProductStateAsync(self, szwProductID, nNewState):
        data = {'szwProductID': szwProductID, 'nNewState': nNewState}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.SetProductStateAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DownloadEventlogAsync(self, szwEventLog):
        data = {'szwEventLog': szwEventLog}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.DownloadEventlogAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CreateAndDownloadDumpAsync(self, szwProcessName):
        data = {'szwProcessName': szwProcessName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.CreateAndDownloadDumpAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DownloadCommonDataAsync(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.DownloadCommonDataAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RunKlnagchkAsync(self, szwProductID):
        data = {'szwProductID': szwProductID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.RunKlnagchkAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ExecuteFileAsync(self, szwURL, szwShortExecName, szwParams):
        data = {'szwURL': szwURL, 'szwShortExecName': szwShortExecName, 'szwParams': szwParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.ExecuteFileAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def ExecuteGsiAsync(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagRdu.ExecuteGsiAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

