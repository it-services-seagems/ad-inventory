# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

""" Basic class for KlAk types. Provides common data, basic methods and general response parsing """

import base64
import json
import http
from .Error import KlAkError, KlAkResponseError
from .Params import KlAkParams, KlAkArray

class KlAkResponse:
    __PxgRetVal = 'PxgRetVal'
    __PxgError = 'PxgError'

    def __init__(self, respose_text): 
        self.respose_text = respose_text
        self.error = None
        self.retval = None
        if type(respose_text) is dict:
            if KlAkResponse.__PxgError in respose_text:
                self.error = respose_text[KlAkResponse.__PxgError]
                raise KlAkError(self.error)
            if KlAkResponse.__PxgRetVal in respose_text:
                self.retval = self.respose_text[KlAkResponse.__PxgRetVal]
                if type(self.retval) is dict:
                    self.retval = KlAkParams(self.retval)
                elif type(self.retval) is list:
                    self.retval = KlAkArray(self.retval)
            self.outpars = {}
            for key, value in self.respose_text.items():
                if not key == KlAkResponse.__PxgRetVal and not key == KlAkResponse.__PxgError:
                    if type(value) is dict:
                        self.outpars[key] = KlAkParams(value)
                    elif type(value) is list:
                        self.outpars[key] = KlAkArray(value) 
                    else:
                        self.outpars[key] = value
                
    def RetVal(self):
        return self.retval
        
    def OutPar(self, par_name):
        if par_name in self.outpars:
            return self.outpars[par_name]
        
    def OutParExists(self, par_name):
        return not self.outpars == None and par_name in self.outpars
        
    def OutPars(self):
        return self.outpars
        
        

class KlAkBase:
    """ KlAkBase supposed to be base class for every other KSC types. Provides general KSC data processing """
    common_headers = {
            'Content-Type': 'application/json',
        }

    def __init__(self):
        pass
    
    def ParseResponse(self, response_code, response_text, retval = True, out_pars = []):
        """ Response parsing, including check for error, return value (retval) presence and output parameters processing """
        
        if response_code != http.HTTPStatus.OK:
            raise KlAkResponseError(response_text)        
            
        text = json.loads(response_text)     
        return KlAkResponse(text)
                
        
def MillisecondsToSeconds(milliseconds):
    return milliseconds * 0.001
           