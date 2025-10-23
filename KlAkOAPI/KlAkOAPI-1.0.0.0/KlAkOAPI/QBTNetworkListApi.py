#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkQBTNetworkListApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def AddListItemTask(self, listName, itemId, taskName, pTaskParams):
        data = {'listName': listName, 'itemId': itemId, 'taskName': taskName, 'pTaskParams': pTaskParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QBTNetworkListApi.AddListItemTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def AddListItemsTask(self, listName, pItemsIds, taskName, pTaskParams):
        data = {'listName': listName, 'pItemsIds': pItemsIds, 'taskName': taskName, 'pTaskParams': pTaskParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QBTNetworkListApi.AddListItemsTask'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetListItemInfo(self, itemId):
        data = {'itemId': itemId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'QBTNetworkListApi.GetListItemInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

