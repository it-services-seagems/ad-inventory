#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkPackagesApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def RecordNewVapmPackageAsync(self, szwNewPackageName, parProductInfo, szwRequestId):
        data = {'szwNewPackageName': szwNewPackageName, 'parProductInfo': parProductInfo, 'szwRequestId': szwRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RecordNewVapmPackageAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def IsPackagePublished(self, nPkgExecId):
        data = {'nPkgExecId': nPkgExecId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.IsPackagePublished'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def PublishStandalonePackage(self, bPublish, nPkgExecId):
        data = {'bPublish': bPublish, 'nPkgExecId': nPkgExecId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.PublishStandalonePackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def PublishMobileManifest(self, nPkgExecId, pAppData):
        data = {'nPkgExecId': nPkgExecId, 'pAppData': pAppData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.PublishMobileManifest'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def PrePublishMobilePackage(self, wstrProfileId):
        data = {'wstrProfileId': wstrProfileId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.PrePublishMobilePackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def PublishMobilePackage(self, wstrProfileId, pProfileData):
        data = {'wstrProfileId': wstrProfileId, 'pProfileData': pProfileData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.PublishMobilePackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def UnpublishMobilePackage(self, wstrProfileId):
        data = {'wstrProfileId': wstrProfileId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.UnpublishMobilePackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CancelRecordNewPackage(self, szwRequestId):
        data = {'szwRequestId': szwRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.CancelRecordNewPackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def AllowSharedPrerequisitesInstallation(self, nPackageId, bAllow):
        data = {'nPackageId': nPackageId, 'bAllow': bAllow}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.AllowSharedPrerequisitesInstallation'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ResolvePackageLcid(self, nPackageId, nLcid):
        data = {'nPackageId': nPackageId, 'nLcid': nLcid}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.ResolvePackageLcid'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetUserAgreements(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetUserAgreements'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RecordVapmPackageAsync(self, szwNewPackageName, parProductInfo):
        data = {'szwNewPackageName': szwNewPackageName, 'parProductInfo': parProductInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RecordVapmPackageAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetPackages(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetPackages'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RenamePackage(self, nPackageId, wstrNewPackageName):
        data = {'nPackageId': nPackageId, 'wstrNewPackageName': wstrNewPackageName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RenamePackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetIntranetFolderForNewPackage(self, wstrProductName, wstrProductVersion):
        data = {'wstrProductName': wstrProductName, 'wstrProductVersion': wstrProductVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetIntranetFolderForNewPackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RecordNewPackage(self, wstrPackageName, wstrFolder, wstrProductName, wstrProductVersion, wstrProductDisplName, wstrProductDisplVersion):
        data = {'wstrPackageName': wstrPackageName, 'wstrFolder': wstrFolder, 'wstrProductName': wstrProductName, 'wstrProductVersion': wstrProductVersion, 'wstrProductDisplName': wstrProductDisplName, 'wstrProductDisplVersion': wstrProductDisplVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RecordNewPackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RecordNewPackage2(self, wstrPackageName, wstrFileId, wstrFolder, wstrProductName, wstrProductVersion, wstrProductDisplName, wstrProductDisplVersion):
        data = {'wstrPackageName': wstrPackageName, 'wstrFileId': wstrFileId, 'wstrFolder': wstrFolder, 'wstrProductName': wstrProductName, 'wstrProductVersion': wstrProductVersion, 'wstrProductDisplName': wstrProductDisplName, 'wstrProductDisplVersion': wstrProductDisplVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RecordNewPackage2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RemovePackage(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RemovePackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetIntranetFolderForPackage(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetIntranetFolderForPackage'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SS_Read(self, wstrStorageDescr, wstrName, wstrVersion, wstrSection, nTimeoutMsec):
        data = {'wstrStorageDescr': wstrStorageDescr, 'wstrName': wstrName, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'nTimeoutMsec': nTimeoutMsec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.SS_Read'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SS_Write(self, wstrStorageDescr, wstrName, wstrVersion, wstrSection, pData, nTimeoutMsec, nOperationType):
        data = {'wstrStorageDescr': wstrStorageDescr, 'wstrName': wstrName, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'pData': pData, 'nTimeoutMsec': nTimeoutMsec, 'nOperationType': nOperationType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.SS_Write'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SS_SectionOperation(self, wstrStorageDescr, wstrName, wstrVersion, wstrSection, nTimeoutMsec, nOperationType):
        data = {'wstrStorageDescr': wstrStorageDescr, 'wstrName': wstrName, 'wstrVersion': wstrVersion, 'wstrSection': wstrSection, 'nTimeoutMsec': nTimeoutMsec, 'nOperationType': nOperationType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.SS_SectionOperation'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SS_GetNames(self, wstrStorageDescr, wstrName, wstrVersion, nTimeoutMsec):
        data = {'wstrStorageDescr': wstrStorageDescr, 'wstrName': wstrName, 'wstrVersion': wstrVersion, 'nTimeoutMsec': nTimeoutMsec}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.SS_GetNames'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RemovePackage2(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RemovePackage2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['bResult', 'pTasks'])

    def GetLoginScript(self, nPackageId, wstrTaskId):
        data = {'nPackageId': nPackageId, 'wstrTaskId': wstrTaskId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetLoginScript'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetLicenseKey(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetLicenseKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrKeyFileName', 'pMemoryChunk'])

    def SetLicenseKey(self, nPackageId, wstrKeyFileName, pData, bRemoveExisting):
        data = {'nPackageId': nPackageId, 'wstrKeyFileName': wstrKeyFileName, 'pData': pData, 'bRemoveExisting': bRemoveExisting}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.SetLicenseKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ReadPkgCfgFile(self, nPackageId, wstrFileName):
        data = {'nPackageId': nPackageId, 'wstrFileName': wstrFileName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.ReadPkgCfgFile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def WritePkgCfgFile(self, nPackageId, wstrFileName, pData):
        data = {'nPackageId': nPackageId, 'wstrFileName': wstrFileName, 'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.WritePkgCfgFile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ReadKpdFile(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.ReadKpdFile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetKpdProfileString(self, nPackageId, wstrSection, wstrKey, wstrDefault):
        data = {'nPackageId': nPackageId, 'wstrSection': wstrSection, 'wstrKey': wstrKey, 'wstrDefault': wstrDefault}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetKpdProfileString'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def WriteKpdProfileString(self, nPackageId, wstrSection, wstrKey, wstrValue):
        data = {'nPackageId': nPackageId, 'wstrSection': wstrSection, 'wstrKey': wstrKey, 'wstrValue': wstrValue}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.WriteKpdProfileString'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetRebootOptionsEx(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetRebootOptionsEx'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RecordNewPackageAsync(self, wstrName, wstrFolder, wstrProductName, wstrProductVersion, wstrProductDisplName, wstrProductDisplVersion):
        data = {'wstrName': wstrName, 'wstrFolder': wstrFolder, 'wstrProductName': wstrProductName, 'wstrProductVersion': wstrProductVersion, 'wstrProductDisplName': wstrProductDisplName, 'wstrProductDisplVersion': wstrProductDisplVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RecordNewPackageAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetPackageInfo(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetPackageInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetIncompatibleAppsInfo(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetIncompatibleAppsInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def SetRemoveIncompatibleApps(self, nPackageId, bRemoveIncompatibleApps):
        data = {'nPackageId': nPackageId, 'bRemoveIncompatibleApps': bRemoveIncompatibleApps}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.SetRemoveIncompatibleApps'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CreateExecutablePkgAsync(self, pData):
        data = {'pData': pData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.CreateExecutablePkgAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CancelCreateExecutablePkg(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.CancelCreateExecutablePkg'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetExecutablePackages(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetExecutablePackages'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteExecutablePkg(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.DeleteExecutablePkg'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetPackages2(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetPackages2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetPackageInfo2(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetPackageInfo2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateBasesInPackagesAsync(self, pParams):
        data = {'pParams': pParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.UpdateBasesInPackagesAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CancelUpdateBasesInPackages(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.CancelUpdateBasesInPackages'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def RetranslateToVServerAsync(self, nPackageId, nVServerId, pOptions):
        data = {'nPackageId': nPackageId, 'nVServerId': nVServerId, 'pOptions': pOptions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RetranslateToVServerAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetMoveRuleInfo(self, nRuleId):
        data = {'nRuleId': nRuleId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetMoveRuleInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetExecutablePkgFileAsync(self, pParams, nPackageId):
        data = {'pParams': pParams, 'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetExecutablePkgFileAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CancelGetExecutablePkgFile(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.CancelGetExecutablePkgFile'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetEulaText(self, nEulaId):
        data = {'nEulaId': nEulaId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetEulaText'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrEulaText'])

    def AcceptEulas(self, vecEulaIDs):
        data = {'vecEulaIDs': vecEulaIDs}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.AcceptEulas'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ResetDefaultServerSpecificSettings(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.ResetDefaultServerSpecificSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddExtendedSign(self, pParams):
        data = {'pParams': pParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.AddExtendedSign'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddExtendedSignAsync(self, pParams, wstrRequestID):
        data = {'pParams': pParams, 'wstrRequestID': wstrRequestID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.AddExtendedSignAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetPackageInfoFromArchive(self, wstrFileId, pOptions):
        data = {'wstrFileId': wstrFileId, 'pOptions': pOptions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetPackageInfoFromArchive'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RecordNewPackage3(self, wstrFileId, pOptions):
        data = {'wstrFileId': wstrFileId, 'pOptions': pOptions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RecordNewPackage3'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def RecordNewPackage3Async(self, wstrFileId, pOptions, wstrRequestID):
        data = {'wstrFileId': wstrFileId, 'pOptions': pOptions, 'wstrRequestID': wstrRequestID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.RecordNewPackage3Async'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetPackagePlugin(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetPackagePlugin'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateCleanerFileAsync(self, nPackageId, wstrRequestId):
        data = {'nPackageId': nPackageId, 'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.UpdateCleanerFileAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def UpdateCleanerFileAsync2(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.UpdateCleanerFileAsync2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CancelUpdateCleanerFileAsync(self, wstrRequestId):
        data = {'wstrRequestId': wstrRequestId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.CancelUpdateCleanerFileAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetPackageInfo3(self, nPackageId):
        data = {'nPackageId': nPackageId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'PackagesApi.GetPackageInfo3'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

