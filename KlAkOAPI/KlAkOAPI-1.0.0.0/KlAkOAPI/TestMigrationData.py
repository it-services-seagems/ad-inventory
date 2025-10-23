#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkTestMigrationData (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def TestExportGroup(self, wstrDstDir, lGroup):
        data = {'wstrDstDir': wstrDstDir, 'lGroup': lGroup}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestExportGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestImportGroup(self, wstrSrcDir, lGroup):
        data = {'wstrSrcDir': wstrSrcDir, 'lGroup': lGroup}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestImportGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def TestExportDeviceQueries(self, wstrDstDir):
        data = {'wstrDstDir': wstrDstDir}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestExportDeviceQueries'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestImportDeviceQueries(self, wstrSrcDir):
        data = {'wstrSrcDir': wstrSrcDir}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestImportDeviceQueries'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestExportCommonTasks(self, wstrDstDir):
        data = {'wstrDstDir': wstrDstDir}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestExportCommonTasks'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestImportCommonTasks(self, wstrSrcDir):
        data = {'wstrSrcDir': wstrSrcDir}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestImportCommonTasks'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestExportCommonReports(self, wstrDstDir):
        data = {'wstrDstDir': wstrDstDir}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestExportCommonReports'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestImportCommonReports(self, wstrSrcDir):
        data = {'wstrSrcDir': wstrSrcDir}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestImportCommonReports'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestExportCustomCategories(self, wstrDstDir, wstrNameFilter):
        data = {'wstrDstDir': wstrDstDir, 'wstrNameFilter': wstrNameFilter}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestExportCustomCategories'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def TestImportCustomCategories(self, wstrSrcDir):
        data = {'wstrSrcDir': wstrSrcDir}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestImportCustomCategories'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def TestVerifyImportedHostAttributes(self, wstrDisplayNamePart):
        data = {'wstrDisplayNamePart': wstrDisplayNamePart}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestVerifyImportedHostAttributes'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def TestCreateEmptyMetadata(self, wstrGroupsFolder):
        data = {'wstrGroupsFolder': wstrGroupsFolder}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'TestMigrationData.TestCreateEmptyMetadata'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

