#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkNagNetworkListApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetListItemFileInfo(self, listName, itemId, bNeedPacked):
        data = {'listName': listName, 'itemId': itemId, 'bNeedPacked': bNeedPacked}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagNetworkListApi.GetListItemFileInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['pFileInfo'])

    def GetListItemFileInfo2(self, listName, itemId, productName, productVersion, bNeedPacked, pOptions):
        data = {'listName': listName, 'itemId': itemId, 'productName': productName, 'productVersion': productVersion, 'bNeedPacked': bNeedPacked, 'pOptions': pOptions}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagNetworkListApi.GetListItemFileInfo2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['pFileInfo'])

    def GetListItemFileChunk(self, listName, itemId, bNeedPacked, ulStartPos, lBytesToRead):
        data = {'listName': listName, 'itemId': itemId, 'bNeedPacked': bNeedPacked, 'ulStartPos': ulStartPos, 'lBytesToRead': lBytesToRead}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagNetworkListApi.GetListItemFileChunk'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['pChunk'])

    def GetListItemFileChunk2(self, listName, itemId, productName, productVersion, pOptions, bNeedPacked, ulStartPos, lBytesToRead):
        data = {'listName': listName, 'itemId': itemId, 'productName': productName, 'productVersion': productVersion, 'pOptions': pOptions, 'bNeedPacked': bNeedPacked, 'ulStartPos': ulStartPos, 'lBytesToRead': lBytesToRead}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'NagNetworkListApi.GetListItemFileChunk2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['pChunk'])

