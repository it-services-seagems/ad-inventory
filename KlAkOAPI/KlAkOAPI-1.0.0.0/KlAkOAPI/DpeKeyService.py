#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkDpeKeyService (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def GetDeviceKey(self, deviceId, pEncryptedKey):
        data = {'deviceId': deviceId, 'pEncryptedKey': pEncryptedKey}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DpeKeyService.GetDeviceKey'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEncryptedDeviceKey'])

    def GetDeviceKeys(self, deviceId, pEncryptedKey):
        data = {'deviceId': deviceId, 'pEncryptedKey': pEncryptedKey}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DpeKeyService.GetDeviceKeys'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pDevicesEncryptionInfo'])

    def GetDeviceKeys2(self, deviceId, pEncryptedKey):
        data = {'deviceId': deviceId, 'pEncryptedKey': pEncryptedKey}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DpeKeyService.GetDeviceKeys2'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pDevicesEncryptionInfo'])

    def UpdateEncryptionInfo(self, wstrHostId, wstrPrstHostId, pEncryptionInfo):
        data = {'wstrHostId': wstrHostId, 'wstrPrstHostId': wstrPrstHostId, 'pEncryptionInfo': pEncryptionInfo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DpeKeyService.UpdateEncryptionInfo'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def PutSlaveServerKeyTest(self, wstrSlvServerId, tCreated, pKey):
        data = {'wstrSlvServerId': wstrSlvServerId, 'tCreated': tCreated, 'pKey': pKey}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DpeKeyService.PutSlaveServerKeyTest'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def GetSlaveServerKeyTest(self, wstrSlvServerId):
        data = {'wstrSlvServerId': wstrSlvServerId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DpeKeyService.GetSlaveServerKeyTest'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pKey'])

    def GetDeviceKeys3(self, wstrDeviceId):
        data = {'wstrDeviceId': wstrDeviceId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'DpeKeyService.GetDeviceKeys3'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pKeyInfos'])

