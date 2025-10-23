#! /usr/bin/python -tt

from .Base import KlAkBase
from .Params import KlAkParamsEncoder
import json

class KlAkEventNotificationsApi (KlAkBase):
    def __init__(self, server, instance = ''):
        self.server = server
        self.instance = instance

    def PublishEvent(self, wstrEventType, pEventBody, tmBirthTime):
        data = {'wstrEventType': wstrEventType, 'pEventBody': pEventBody, 'tmBirthTime': tmBirthTime}
        response = self.server.session.post(url = self.server.Call((lambda: self.instance + '.' if self.instance != None and self.instance != '' else '')() + 'EventNotificationsApi.PublishEvent'), headers = KlAkBase.common_headers, data = json.dumps(data, cls = KlAkParamsEncoder))
        return self.ParseResponse(response.status_code, response.text, retval = False)

