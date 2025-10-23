#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkKsnInternal (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def VerifyNKsnSettings(self, pSettings):
        data = {'pSettings': pSettings}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.VerifyNKsnSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, out_pars=['ppResult'])

    def GetNKsnEula(self, wstrNKsnLoc):
        data = {'wstrNKsnLoc': wstrNKsnLoc}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.GetNKsnEula'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pEula'])

    def GetNKsnEulas(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.GetNKsnEulas'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pNKsnEulas'])

    def GetNKsnSettings(self, szwNKsnLoc):
        data = {'szwNKsnLoc': szwNKsnLoc}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.GetNKsnSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['ppResult'])

    def SendKsnStatisticsViaKsc0(self, pStat):
        data = {'pStat': pStat}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.SendKsnStatisticsViaKsc0'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def CheckKsnConnection(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.CheckKsnConnection'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def GetSettings(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.GetSettings'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pSettings'])

    def SendKsnStatistics(self, wstrStatName, pStatBody):
        data = {'wstrStatName': wstrStatName, 'pStatBody': pStatBody}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.SendKsnStatistics'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

    def NeedToSendStatistics(self):
        data = {}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.NeedToSendStatistics'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text)

    def VerifyKpsnConfigAndGetContentViaKsc0(self, pKpsnConfigPkcs7):
        data = {'pKpsnConfigPkcs7': pKpsnConfigPkcs7}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.VerifyKpsnConfigAndGetContentViaKsc0'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['pRawContentOut'])

    def VerifyKpsnConfigLoc(self, pKpsnConfigPkcs7, wstrLoc):
        data = {'pKpsnConfigPkcs7': pKpsnConfigPkcs7, 'wstrLoc': wstrLoc}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'KsnInternal.VerifyKpsnConfigLoc'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False, out_pars=['ppResult'])

