#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkUserDevicesApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def UpdateDevice(self, lDeviceId, pDevice):
        data = {'lDeviceId': lDeviceId, 'pDevice': pDevice}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.UpdateDevice'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetDevice(self, lDeviceId):
        data = {'lDeviceId': lDeviceId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetDevice'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetDevices(self, pUserId):
        data = {'pUserId': pUserId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetDevices'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetLatestDeviceActivityDate(self, lDeviceId):
        data = {'lDeviceId': lDeviceId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetLatestDeviceActivityDate'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteDevice(self, lDeviceId):
        data = {'lDeviceId': lDeviceId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.DeleteDevice'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GlueDevices(self, lDevice1Id, lDevice2Id):
        data = {'lDevice1Id': lDevice1Id, 'lDevice2Id': lDevice2Id}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GlueDevices'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CreateEnrollmentPackage(self, pUserId, lMdmProtocols, lDeliveryType, lLiveTime, c_wstrUrlFormat):
        data = {'pUserId': pUserId, 'lMdmProtocols': lMdmProtocols, 'lDeliveryType': lDeliveryType, 'lLiveTime': lLiveTime, 'c_wstrUrlFormat': c_wstrUrlFormat}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.CreateEnrollmentPackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetEnrollmentPackages(self, pUserId):
        data = {'pUserId': pUserId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetEnrollmentPackages'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetEnrollmentPackage(self, llEnrPkgId):
        data = {'llEnrPkgId': llEnrPkgId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetEnrollmentPackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteEnrollmentPackage(self, lEnrPkgId):
        data = {'lEnrPkgId': lEnrPkgId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.DeleteEnrollmentPackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetEnrollmentPackageFileInfo(self, c_wstrPackageId, c_wstrUserAgent, c_wstrPackageFileType):
        data = {'c_wstrPackageId': c_wstrPackageId, 'c_wstrUserAgent': c_wstrUserAgent, 'c_wstrPackageFileType': c_wstrPackageFileType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetEnrollmentPackageFileInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetEnrollmentPackageFileData(self, c_wstrPackageId, c_wstrPackageFileType, lBuffOffset, lBuffSize):
        data = {'c_wstrPackageId': c_wstrPackageId, 'c_wstrPackageFileType': c_wstrPackageFileType, 'lBuffOffset': lBuffOffset, 'lBuffSize': lBuffSize}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetEnrollmentPackageFileData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def PostCommand(self, lDeviceId, c_wstrCommandGuid, c_wstrCommandType, pArguments, lMdmProtocols, lProcessFlags):
        data = {'lDeviceId': lDeviceId, 'c_wstrCommandGuid': c_wstrCommandGuid, 'c_wstrCommandType': c_wstrCommandType, 'pArguments': pArguments, 'lMdmProtocols': lMdmProtocols, 'lProcessFlags': lProcessFlags}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.PostCommand'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def RecallCommand(self, c_wstrCommandGuid):
        data = {'c_wstrCommandGuid': c_wstrCommandGuid}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.RecallCommand'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetCommands(self, lDeviceId):
        data = {'lDeviceId': lDeviceId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetCommands'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteCommand(self, c_wstrCommandGuid, bForced):
        data = {'c_wstrCommandGuid': c_wstrCommandGuid, 'bForced': bForced}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.DeleteCommand'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetCommandsLibrary(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetCommandsLibrary'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetDecipheredCommandList(self, llCommandFlags, pCommandsLibrary):
        data = {'llCommandFlags': llCommandFlags, 'pCommandsLibrary': pCommandsLibrary}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetDecipheredCommandList'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GenerateQRCode(self, strInputData, lQRCodeSize, lImageFormat):
        data = {'strInputData': strInputData, 'lQRCodeSize': lQRCodeSize, 'lImageFormat': lImageFormat}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GenerateQRCode'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetJournalRecords(self, lDeviceId):
        data = {'lDeviceId': lDeviceId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetJournalRecords'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSyncInfo(self, nGroupId, nGSyncId, pFields):
        data = {'nGroupId': nGroupId, 'nGSyncId': nGSyncId, 'pFields': pFields}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetSyncInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetMobileAgentSettingStorageData(self, lDeviceId, c_wstrSectionName):
        data = {'lDeviceId': lDeviceId, 'c_wstrSectionName': c_wstrSectionName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetMobileAgentSettingStorageData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetMultitenancyServersInfo(self, nProtocolIds):
        data = {'nProtocolIds': nProtocolIds}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetMultitenancyServersInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetMultitenancyServerSettings(self, c_wstrMtncServerId):
        data = {'c_wstrMtncServerId': c_wstrMtncServerId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetMultitenancyServerSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetMultitenancyServerSettings(self, c_wstrMtncServerId, pSettings):
        data = {'c_wstrMtncServerId': c_wstrMtncServerId, 'pSettings': pSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.SetMultitenancyServerSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CreateEnrollmentPackage2(self, pUserId, lMdmProtocols, lContentType, lLiveTime, c_wstrUrlFormat, pRecipient, pNotification, pProtSpecInfo):
        data = {'pUserId': pUserId, 'lMdmProtocols': lMdmProtocols, 'lContentType': lContentType, 'lLiveTime': lLiveTime, 'c_wstrUrlFormat': c_wstrUrlFormat, 'pRecipient': pRecipient, 'pNotification': pNotification, 'pProtSpecInfo': pProtSpecInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.CreateEnrollmentPackage2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetDevicesExtraData(self, pDeviceIds, pCategories):
        data = {'pDeviceIds': pDeviceIds, 'pCategories': pCategories}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetDevicesExtraData'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSafeBrowserAutoinstallFlag(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetSafeBrowserAutoinstallFlag'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetSafeBrowserAutoinstallFlag(self, bInstall):
        data = {'bInstall': bInstall}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.SetSafeBrowserAutoinstallFlag'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SspLoginAllowed(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.SspLoginAllowed'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetJournalRecords2(self, lDeviceId):
        data = {'lDeviceId': lDeviceId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetJournalRecords2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetJournalCommandResult(self, llJrnlId):
        data = {'llJrnlId': llJrnlId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetJournalCommandResult'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SaveEulaAndAccept(self, wstrProdName, wstrProdVersion, wstrProdDispName, wstrProdDispVersion, binEulaUID, wstrText, tTimeStamp, bAccept):
        data = {'wstrProdName': wstrProdName, 'wstrProdVersion': wstrProdVersion, 'wstrProdDispName': wstrProdDispName, 'wstrProdDispVersion': wstrProdDispVersion, 'binEulaUID': binEulaUID, 'wstrText': wstrText, 'tTimeStamp': tTimeStamp, 'bAccept': bAccept}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.SaveEulaAndAccept'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def IsEulaAccepted(self, binEulaUID):
        data = {'binEulaUID': binEulaUID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.IsEulaAccepted'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetNotAcceptedEulaIds(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetNotAcceptedEulaIds'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetHostsUmdmInfo(self, pHosts):
        data = {'pHosts': pHosts}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'UserDevicesApi.GetHostsUmdmInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

