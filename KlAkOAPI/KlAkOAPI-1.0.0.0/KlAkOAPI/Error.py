# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

""" Exceptions that can be raised due to KSC bad response and/or KSC errors """

import re

class KlAkBaseError(Exception):
    """ Basic Exception/Error. Is not raised anywhere as is, can be uses to catch all types of errors caused by KlAk """
    def __init__(self, data):
        self.data = data

class KlAkError(KlAkBaseError):
    """ KSC Exception / Error that can be received from KLOAPI calls """
    def __init__(self, data):        
        self.data = data
        
        self.code = None
        self.subcode = None
        self.module = None
        self.file = None
        self.line = None
        self.message = None
        self.locdata = None
        self.loc_message = None
        self.locdata_format = None
        self.locdata_format_id = None
        self.locdata_locmodule = None
        self.locdata_args = None
        
        if not type(data) is dict:
            return
            
        if 'code' in data:
            self.code = data['code']
        if 'subcode' in data:
            self.subcode = data['subcode']
        if 'module' in data:
            self.module = data['module']
        if 'file' in data:
            self.file = data['file']
        if 'line' in data:
            self.line = data['line']
        if 'message' in data:
            self.message = data['message']
 
        if 'locdata' in data:  
            err_loc_params = data['locdata'] 
            # parse params structure inplace to avoid circular dependencies with KlAkParams
            if type(err_loc_params) is dict and 'type' in err_loc_params and 'value' in err_loc_params and err_loc_params['type'] == 'params':
                self.locdata = err_loc_params['value']
                if 'format' in self.locdata:
                    self.locdata_format = self.locdata['format']
                if 'format-id' in self.locdata:
                    self.locdata_format_id = self.locdata['format-id']
                if 'locmodule' in self.locdata:
                    self.locdata_locmodule = self.locdata['locmodule']
                if 'args' in self.locdata:
                    self.locdata_args = self.locdata['args']
                if self.locdata_args == None or len(self.locdata_args) == 0:
                    self.loc_message = self.locdata_format
                else:
                    # format localized error description with args
                    template  = r'%(\d+)'
                    template_new = r'%(\1)s'
                    m = re.findall( template, self.locdata_format)
                    if len(m) == 0:
                        # no templates - use localized message as is, no substitutions needed
                        self.loc_message = self.locdata_format
                    else:
                        # format template: transform (format = 'test for %1, %2', args=['arg1', 'arg2']) into substitution expression ('test for %(1)s, %(2)s' % {'1': 'arg1', '2': 'arg2'}))
                        err_format_new = re.sub( template, template_new, self.locdata_format)
                        err_args_dict = {str(i+1) : value for (i, value) in enumerate(self.locdata_args)}
                        err_args_dict.update({group: '' for group in m if (not group in err_args_dict)})
                        self.loc_message = err_format_new % err_args_dict                  
                               
    def __str__(self):
        if self.code == None:
            return str(self.data)
        
        err_description = 'Error code ' + str(self.code)
        if self.loc_message != None:
            err_description += ": " + self.loc_message
        elif self.message != None:
            err_description += ": " + self.message
        
        return err_description


class KlAkResponseError(KlAkBaseError):
    """ KlAkResponseError is raised when HTTP request's Status code differs from 200(OK) or unexpected values found while respose parsing """
    def __init__(self, data):
        self.data = data
        
class KlAkParamTypeError(KlAkBaseError):
    """ KlAkParamTypeError is raised when trying to compose KlAkParams with unappropriate data types """
    def __init__(self, data = ''):
        self.data = data
        if data == '':
            self.data = 'Unexpected data type'
            
