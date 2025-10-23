#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkFilesAcceptor (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def InitiateFileUpload(self, bIsArchive, qwFileSize):
        data = {'bIsArchive': bIsArchive, 'qwFileSize': qwFileSize}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FilesAcceptor.InitiateFileUpload'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['wstrFileId', 'wstrUploadURL'])

    def CancelFileUpload(self, wstrFileId):
        data = {'wstrFileId': wstrFileId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'FilesAcceptor.CancelFileUpload'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

