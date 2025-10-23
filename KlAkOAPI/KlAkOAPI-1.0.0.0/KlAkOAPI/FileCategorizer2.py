#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkFileCategorizer2 (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def CreateCategory(self, pCategory):
        data = {'pCategory': pCategory}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.CreateCategory'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetCategory(self, nCategoryId):
        data = {'nCategoryId': nCategoryId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetCategory'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pCategory'])

    def GetCategoryByUUID(self, pCategoryUUID):
        data = {'pCategoryUUID': pCategoryUUID}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetCategoryByUUID'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pCategory'])

    def UpdateCategory(self, nCategoryId, pCategory):
        data = {'nCategoryId': nCategoryId, 'pCategory': pCategory}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.UpdateCategory'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteCategory(self, nCategoryId):
        data = {'nCategoryId': nCategoryId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.DeleteCategory'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ForceCategoryUpdate(self, nCategoryId):
        data = {'nCategoryId': nCategoryId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.ForceCategoryUpdate'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DoStaticAnalysisAsync(self, wstrRequestId, nPolicyId):
        data = {'wstrRequestId': wstrRequestId, 'nPolicyId': nPolicyId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.DoStaticAnalysisAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DoStaticAnalysisAsync2(self, nPolicyId):
        data = {'nPolicyId': nPolicyId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.DoStaticAnalysisAsync2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

    def DoTestStaticAnalysisAsync(self, wstrRequestId, nPolicyId, pTestACL):
        data = {'wstrRequestId': wstrRequestId, 'nPolicyId': nPolicyId, 'pTestACL': pTestACL}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.DoTestStaticAnalysisAsync'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DoTestStaticAnalysisAsync2(self, nPolicyId, pTestACL):
        data = {'nPolicyId': nPolicyId, 'pTestACL': pTestACL}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.DoTestStaticAnalysisAsync2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

    def FinishStaticAnalysis(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.FinishStaticAnalysis'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetSerializedCategoryBody(self, nCategoryId):
        data = {'nCategoryId': nCategoryId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetSerializedCategoryBody'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pCategory'])

    def GetSerializedCategoryBody2(self, nCategoryId):
        data = {'nCategoryId': nCategoryId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetSerializedCategoryBody2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pCategory'])

    def GetCategoriesModificationCounter(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetCategoriesModificationCounter'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSyncId(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetSyncId'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetRefPolicies(self, nCatId):
        data = {'nCatId': nCatId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetRefPolicies'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pPolicies'])

    def AddFiles(self, nCatId, arrFiles):
        data = {'nCatId': nCatId, 'arrFiles': arrFiles}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.AddFiles'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def RemoveFiles(self, nCatId, arrFiles):
        data = {'nCatId': nCatId, 'arrFiles': arrFiles}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.RemoveFiles'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def WaitForTestCmdExecute(self, nCatId):
        data = {'nCatId': nCatId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.WaitForTestCmdExecute'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ExportCategory(self, nCatId, wstrFileName):
        data = {'nCatId': nCatId, 'wstrFileName': wstrFileName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.ExportCategory'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def ImportCategory(self, wstrFileName):
        data = {'wstrFileName': wstrFileName}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.ImportCategory'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def InitFileUpload(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.InitFileUpload'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrUploadUrl'])

    def CancelFileUpload(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.CancelFileUpload'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetFileMetadata(self, ulFlag):
        data = {'ulFlag': ulFlag}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetFileMetadata'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

    def GetFilesMetadata(self, ulFlag):
        data = {'ulFlag': ulFlag}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetFilesMetadata'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

    def GetFilesMetadataFromMSI(self, ulFlag):
        data = {'ulFlag': ulFlag}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.GetFilesMetadataFromMSI'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

    def CancelFileMetadataOperations(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.CancelFileMetadataOperations'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def AddExpressions(self, nCategoryId, arrNewExpressions, bInclusions):
        data = {'nCategoryId': nCategoryId, 'arrNewExpressions': arrNewExpressions, 'bInclusions': bInclusions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.AddExpressions'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

    def UpdateExpressions(self, nCategoryId, arrIdAndExpression, bInclusions):
        data = {'nCategoryId': nCategoryId, 'arrIdAndExpression': arrIdAndExpression, 'bInclusions': bInclusions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.UpdateExpressions'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

    def DeleteExpression(self, nCategoryId, arrIds, bInclusions):
        data = {'nCategoryId': nCategoryId, 'arrIds': arrIds, 'bInclusions': bInclusions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FileCategorizer2.DeleteExpression'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrAsyncId'])

