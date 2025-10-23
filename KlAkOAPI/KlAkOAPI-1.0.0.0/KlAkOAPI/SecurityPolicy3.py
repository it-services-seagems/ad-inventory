#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkSecurityPolicy3 (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def AddSecurityGroup(self, pGrpParams, lVsId):
        data = {'pGrpParams': pGrpParams, 'lVsId': lVsId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.AddSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def UpdateSecurityGroup(self, lGrpId, pGrpParams):
        data = {'lGrpId': lGrpId, 'pGrpParams': pGrpParams}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.UpdateSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteSecurityGroup(self, lGrpId):
        data = {'lGrpId': lGrpId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.DeleteSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def AddUserIntoSecurityGroup(self, lUserId, lGrpId):
        data = {'lUserId': lUserId, 'lGrpId': lGrpId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.AddUserIntoSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteUserFromSecurityGroup(self, lUserId, lGrpId):
        data = {'lUserId': lUserId, 'lGrpId': lGrpId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.DeleteUserFromSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def MoveUserIntoOtherSecurityGroup(self, lUserId, lGrpIdFrom, lGrpIdTo):
        data = {'lUserId': lUserId, 'lGrpIdFrom': lGrpIdFrom, 'lGrpIdTo': lGrpIdTo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.MoveUserIntoOtherSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def AddTrusteeIntoSecurityGroup(self, llTrusteeId, lGrpId):
        data = {'llTrusteeId': llTrusteeId, 'lGrpId': lGrpId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.AddTrusteeIntoSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def DeleteTrusteeFromSecurityGroup(self, llTrusteeId, lGrpId):
        data = {'llTrusteeId': llTrusteeId, 'lGrpId': lGrpId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.DeleteTrusteeFromSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def MoveTrusteeIntoOtherSecurityGroup(self, llTrusteeId, lGrpIdFrom, lGrpIdTo):
        data = {'llTrusteeId': llTrusteeId, 'lGrpIdFrom': lGrpIdFrom, 'lGrpIdTo': lGrpIdTo}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.MoveTrusteeIntoOtherSecurityGroup'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CloseUserConnections(self, lUserId):
        data = {'lUserId': lUserId}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'SecurityPolicy3.CloseUserConnections'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

