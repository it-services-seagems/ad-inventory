#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkHstAccessControl (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def ModifyScObjectAcl(self, nObjId, nObjType, pAclParams, bCheckCurrentUserAce):
        data = {'nObjId': nObjId, 'nObjType': nObjType, 'pAclParams': pAclParams, 'bCheckCurrentUserAce': bCheckCurrentUserAce}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.ModifyScObjectAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SetScObjectAcl(self, nObjId, nObjType, pAclParams, bCheckCurrentUserAce):
        data = {'nObjId': nObjId, 'nObjType': nObjType, 'pAclParams': pAclParams, 'bCheckCurrentUserAce': bCheckCurrentUserAce}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.SetScObjectAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def SetScVServerAcl(self, nId, pAclParams, bCheckCurrentUserAce):
        data = {'nId': nId, 'pAclParams': pAclParams, 'bCheckCurrentUserAce': bCheckCurrentUserAce}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.SetScVServerAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetScObjectAcl(self, nObjId, nObjType):
        data = {'nObjId': nObjId, 'nObjType': nObjType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetScObjectAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pAclParams'])

    def GetScVServerAcl(self, nId):
        data = {'nId': nId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetScVServerAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pAclParams'])

    def DeleteScObjectAcl(self, nObjId, nObjType):
        data = {'nObjId': nObjId, 'nObjType': nObjType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.DeleteScObjectAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteScVServerAcl(self, nId):
        data = {'nId': nId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.DeleteScVServerAcl'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetVisualViewForAccessRights(self, wstrLangCode, nObjId, nObjType):
        data = {'wstrLangCode': wstrLangCode, 'nObjId': nObjId, 'nObjType': nObjType}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetVisualViewForAccessRights'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pViewParams'])

    def AccessCheckToAdmGroup(self, lGroupId, dwAccessMask, szwFuncArea, szwProduct, szwVersion):
        data = {'lGroupId': lGroupId, 'dwAccessMask': dwAccessMask, 'szwFuncArea': szwFuncArea, 'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.AccessCheckToAdmGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetAccessibleFuncAreas(self, lGroupId, dwAccessMask, szwProduct, szwVersion, bInvert):
        data = {'lGroupId': lGroupId, 'dwAccessMask': dwAccessMask, 'szwProduct': szwProduct, 'szwVersion': szwVersion, 'bInvert': bInvert}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetAccessibleFuncAreas'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pFuncAreasArray'])

    def GetMappingFuncAreaToPolicies(self, szwProduct, szwVersion):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetMappingFuncAreaToPolicies'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetMappingFuncAreaToSettings(self, szwProduct, szwVersion):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetMappingFuncAreaToSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetMappingFuncAreaToTasks(self, szwProduct, szwVersion):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetMappingFuncAreaToTasks'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetMappingFuncAreaToReports(self, szwProduct, szwVersion):
        data = {'szwProduct': szwProduct, 'szwVersion': szwVersion}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetMappingFuncAreaToReports'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def AddRole(self, pRoleData):
        data = {'pRoleData': pRoleData}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.AddRole'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateRole(self, nId, pRoleData, bProtection):
        data = {'nId': nId, 'pRoleData': pRoleData, 'bProtection': bProtection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.UpdateRole'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def DeleteRole(self, nId, bProtection):
        data = {'nId': nId, 'bProtection': bProtection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.DeleteRole'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetRole(self, nId, pFieldsToReturn):
        data = {'nId': nId, 'pFieldsToReturn': pFieldsToReturn}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetRole'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def FindRoles(self, strFilter, pFieldsToReturn, pFieldsToOrder, lMaxLifeTime):
        data = {'strFilter': strFilter, 'pFieldsToReturn': pFieldsToReturn, 'pFieldsToOrder': pFieldsToOrder, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.FindRoles'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['strAccessor'])

    def GetTrustee(self, nId, pFieldsToReturn):
        data = {'nId': nId, 'pFieldsToReturn': pFieldsToReturn}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetTrustee'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def FindTrustees(self, strFilter, pFieldsToReturn, pFieldsToOrder, lMaxLifeTime):
        data = {'strFilter': strFilter, 'pFieldsToReturn': pFieldsToReturn, 'pFieldsToOrder': pFieldsToOrder, 'lMaxLifeTime': lMaxLifeTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.FindTrustees'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['strAccessor'])

    def GetPolicyReadonlyNodes(self, lGroupId, szwProduct, szwVersion, szwSectionName, pPolicySection):
        data = {'lGroupId': lGroupId, 'szwProduct': szwProduct, 'szwVersion': szwVersion, 'szwSectionName': szwSectionName, 'pPolicySection': pPolicySection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetPolicyReadonlyNodes'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSettingsReadonlyNodes(self, lGroupId, szwProduct, szwVersion, szwSectionName, pSettingsSection):
        data = {'lGroupId': lGroupId, 'szwProduct': szwProduct, 'szwVersion': szwVersion, 'szwSectionName': szwSectionName, 'pSettingsSection': pSettingsSection}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.GetSettingsReadonlyNodes'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def IsTaskTypeReadonly(self, lGroupId, szwProduct, szwVersion, szwTaskTypeName):
        data = {'lGroupId': lGroupId, 'szwProduct': szwProduct, 'szwVersion': szwVersion, 'szwTaskTypeName': szwTaskTypeName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.IsTaskTypeReadonly'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def CheckEffectiveRights(self, nVServerId, llTrusteeId, szwProduct, szwVersion, pAccessRights):
        data = {'nVServerId': nVServerId, 'llTrusteeId': llTrusteeId, 'szwProduct': szwProduct, 'szwVersion': szwVersion, 'pAccessRights': pAccessRights}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'HstAccessControl.CheckEffectiveRights'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

