# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

from json import JSONEncoder
from datetime import datetime, date
import base64
import copy
from .Error import KlAkError, KlAkParamTypeError


TypeToWord = {'paramString': '', 'paramInt': '', 'paramBool': '', 'paramArray' : '', 'paramLong': 'long', 'paramDateTime': 'datetime', 'paramDate' : 'date', 'paramBinary': 'binary', 'paramFloat': 'float', 'paramDouble': 'double', 'paramParams': 'params'}

def paramString(value):
    if not type(value) is str:
        raise KlAkParamTypeError('paramString expects str datatype, while ' + str(type(value)) + ' is given')
    return value
   
def paramBool(value):
    if not type(value) is bool:
        raise KlAkParamTypeError('paramBool expects bool datatype, while ' + str(type(value)) + ' is given')
    return value
    
def paramInt(value):
    if not type(value) is int:
        raise KlAkParamTypeError('paramInt expects int datatype, while ' + str(type(value)) + ' is given')
    return value
    
def paramLong(value):
    if not type(value) is int:
        raise KlAkParamTypeError('paramLong expects int datatype, while ' + str(type(value)) + ' is given')
    return {'type': TypeToWord[paramLong.__name__], 'value': value}
    
def dateTimeToStr(value):
    if type(value) is datetime:
        return value.isoformat(timespec='seconds') + 'Z'
    
def strToDateTime(value):
    if type(value) is str:
       return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')    
    
def paramDateTime(value):
    if not type(value) in [str, datetime]:
        raise KlAkParamTypeError('paramDateTime expects str OR datetime datatype, while ' + str(type(value)) + ' is given')
    if type(value) is datetime:
        value = dateTimeToStr(value)
    else:
        try:
            strToDateTime(value)  # ValueError exception is raised if datetime cannot be parsed correctly
        except ValueError as err:
            raise KlAkParamTypeError('paramDateTime expects string in format <YYYY-MM-DDTHH:MM:SSZ> or datetime object')
    return {'type': TypeToWord[paramDateTime.__name__], 'value': value}

def dateToStr(value):
    if type(value) is date:
        return value.isoformat()
        
def strToDate(value):
    if type(value) is str:
        return datetime.strptime(value, '%Y-%m-%d').date()
        
def paramDate(value):  
    if not type(value) in [str, date, datetime]:
        raise KlAkParamTypeError('paramDate expects str OR date OR datetime datatype, while ' + str(type(value)) + ' is given')
    if type(value) is date:
        value = dateToStr(value)
    elif type(value) is datetime:
        value = dateToStr(value.date())
    else:
        try:
            strToDate(value)  # ValueError exception is raised  if datetime cannot be parsed correctly
        except ValueError as err:
            raise KlAkParamTypeError('paramDate expects string in format <YYYY-MM-DD> or datetime or date object')
    return {'type': TypeToWord[paramDate.__name__], 'value': value}

def binToStr(value):
    if type(value) is bytes:
        return base64.b64encode(value).decode("utf-8")

def strToBin(value):
    if type(value) is str:
        return base64.b64decode(value)

def paramBinary(value):
    if not type(value) in [str, bytes]:
        raise KlAkParamTypeError('paramBinary expects str datatype, while ' + str(type(value)) + ' is given')
    if type(value) is bytes:
        value = binToStr(value)
    return {'type': TypeToWord[paramBinary.__name__], 'value': value} 

def paramFloat(value):
    if not type(value) is float:
        raise KlAkParamTypeError('paramFloat expects float datatype, while ' + str(type(value)) + ' is given')
    return {'type': TypeToWord[paramFloat.__name__], 'value': value}
    
def paramDouble(value):   
    if not type(value) is float:  # float in python has double precision, same as double datatype in C/Java
        raise KlAkParamTypeError('paramDouble expects float datatype, while ' + str(type(value)) + ' is given')
    return {'type': TypeToWord[paramDouble.__name__], 'value': value}
    
def paramParams(value):
    """ Checks value to correspond params datatype and returns dict in paramParams format that can be used in KlAkParams.AddParams(...) method """
    if not type(value) in [dict, KlAkParams]:
        raise KlAkParamTypeError('paramParams expects dict OR KlAkParams datatype, while ' + str(type(value)) + ' is given')
    
    if type(value) is KlAkParams:
        value_checked_type = value.data
    else:
        # check elems for Null value - Null is not acceptable in params
        if not all(elem != None for elem in value.values()):
            raise KlAkParamTypeError('paramParams does not support None value')    
        # check param structure in every elem & unwrap KlAkArray into dict
        value_checked_type = {}
        for key, data in value.items():
            value_checked_type.update(KlAkParams({key: data}).data)
    
    return {'type': TypeToWord[paramParams.__name__], 'value': value_checked_type}
        
def paramArray(value):
    """ Checks array elements format to correspond params datatypes and returns dict in paramArray format that can be used in KlAkParams.AddArray(...) method.
        Value can be either list or KlAkArray or a value of params type - in last case a list of one element is formed """
    if type(value) is KlAkArray:
        return value.data
    if type(value) is list:
        value_list = value
    else:
        value_list = [value]
    return KlAkArray(value_list).data
        
def IsParamTypeWord(word):
    """ Returns True if word is used as type word in KLOAPI ('long', 'datetime', 'binary', 'params', etc.) otherwise returns False """
    return  word != '' and word in list(TypeToWord.values())

def IsParamType(value):
    """ Returns True if value represents correct Params structure, i.e. contains simple type (str, int or bool), 
    or contains dict with proper structure ({'type': one of type words ('long', 'params', etc), 'value': value of correspondent type)  
    or contains list each element of which has a proper Params structure """
    if type(value) in [str, bool, int]:
        return True
    if type(value) is dict and 'type' in value and 'value' in value and IsParamTypeWord(value['type']):
        return True
    if type(value) is KlAkArray:
        return True
    if type(value) is list:
        isValueParamType = True    
        for elem in value:
            isValueParamType = isValueParamType and (IsParamType(elem) or (elem == None))
        return isValueParamType
    # KlAkParams not allowed here, cause it is params type, not paramParams type        
        
    return False
            
def extractParamValue(value):
    """ Returns value from params structure: i.e. returns float number 1.2 for dict {type: float, value: 1.2} , etc. Is used in KlAkArray and KlAkParams """
    if type(value) in [str, int, bool]:
        return value
    elif type(value) is list:
        return KlAkArray(value)
    elif type(value) is dict and 'type' in value and 'value' in value and IsParamTypeWord(value['type']):
        if value['type'] == 'long':
            return value['value']
        elif value['type'] == 'float':
            return value['value']
        elif value['type'] == 'double':
            return value['value']
        elif value['type'] == 'binary':
            return strToBin(value['value'])
        elif value['type'] == 'datetime':
            if value['value'] == '':
                return ''
            return strToDateTime(value['value'])
        elif value['type'] == 'date':
            if value['value'] == '':
                return ''
            return strToDate(value['value'])
        elif value['type'] == 'params':
            return KlAkParams(value['value'])
                
        raise KlAkParamTypeError('KlAkParams object''s section <'+ name + '> has inappropriate type.')
       

def paramXXX(value):
    """ Wraps value into param-converter, selected by value type, such as: dict is wrapped into paramParams, datetime is wrapped into paramDateTime, bytes is wrapped into paramBinary, etc.
    Attention! This method can not distinguish int / long and float / double datatypes, it always wrap int value into paramInt wrapper and float value into paramDouble wrapper """    
    if type(value) in [int, str, bool]:
        return value
    if type(value) is float:
        return paramDouble(value)
    elif type(value) is dict:
        if 'type' in value and 'value' in value and IsParamTypeWord(value['type']):
            return value
        else:
            return paramParams(value)
    elif type(value) is KlAkParams:
        return paramParams(value.data)
    elif type(value) is date:
        return paramDate(value)
    elif type(value) is datetime:
        return paramDateTime(value)
    elif type(value) is bytes:
        return paramBinary(value)
    elif type(value) is KlAkArray:
        return value.data
    elif type(value) is list:
        return paramArray(value)
        
  
####

class KlAkArray:
    """ KlAkArray provides methods for composing, parsing, type checking for Array KLOAPI data type """
    def __init__(self, data = []):
        self.data = []
        if data == None:
            return
        if type(data) is KlAkArray:
            self.data = copy.deepcopy(data.data)
            return
        if not type(data) is list:
            data = [data]
        for i, elem in enumerate(data):
            # check type of every element
            if elem == None:
                self.data.append(elem)
            elif type(elem) is KlAkArray:
                self.data.append(elem.data)
            else:
                if IsParamType(elem):
                    self.data.append(elem)
                else:
                    wrapped_elem = paramXXX(elem)
                    if wrapped_elem == None:
                        raise KlAkParamTypeError('KlAkArray does not support datatype ' + str(type(elem)) + ' used for ' + str(i) + '-th element. Please use paramInt/paramLong/paramStr or other converters to construct params values')
                    self.data.append(wrapped_elem)
        
        
    def __repr__(self):
        return repr(self.data)    

    def __len__(self):
        return len(self.data)
        
    def AddString(self, value):
        """ Add a value of type str, treat as paramString value """
        self.data.append(paramString(value))
        
    def AddBool(self, value):
        """ Add a value of type bool, treat as paramBool value """
        self.data.append(paramBool(value))       
       
    def AddInt(self, value):
        """ Add a value of type int, treat as paramInt value """
        self.data.append(paramInt(value))    
        
    def AddLong(self, value):
        """ Add a value of type int, contains paramLong-wrapper inside """
        self.data.append(paramLong(value))  
       
    def AddDateTime(self, value):
        """ Add a value of type datetime or str (in case of str performs check for datetime format, otherwise transforms data to string of proper format) and contains paramDateTime-wrapper inside """
        self.data.append(paramDateTime(value))   
        
    def AddDate(self, value):
        """ Add a value of type date or datetime or str (in case of str performs check for date format, otherwise transforms data to string of proper format) and contains paramDate-wrapper inside """
        self.data.append(paramDate(value))   
        
    def AddBinary(self, value):
        """ Add a value of type str or bytes (in case of bytes performs base64 encoding) and contains paramBinary-wrapper inside """
        self.data.append(paramBinary(value))   
    
    def AddFloat(self, value):
        """ Add a value of type float, contains paramFloat-wrapper inside """
        self.data.append(paramFloat(value))    
    
    def AddDouble(self, value):
        """ Add a value of type float, treated as double (builtin float type in python corresponds to double in C\Java) contains paramDoule-wrapper inside """
        self.data.append(paramDouble(value))  
       
    def AddParams(self, value):
        """ Add a value of type KlAkParams or dict which structure corresponds to params (not paramParams) structure: contains paramParams-wrapper inside """
        self.data.append(paramParams(value))
    
    def AddArray(self, value):
        """ Add a value of type KlAkArray or list which contents corresponds to paramParams structure """
        self.data.append(paramArray(value))

    def Add(self, value):     
        """ Add a value that was retrieved from another KlAkParams/KlAkArray object with GetValue(...) method or raw dict which contents corresponds to paramString/paramsInt/.../paramArray/paramParams structure """    
        if IsParamType(value):
            self.data.append(value) 
        else:
            raise KlAkParamTypeError('KlAkArray cannot accept value with inproper structure for ' + str(len(self) - 1) + '-th elem.')
          
    def GetType(self, index):
        """ Returns type of element of array (i.e. 'paramString', 'paramsLong', 'paramParams', etc. """
        if not type(index) is int:
            raise TypeError
        if index < 0:  # treat as count backwards from end to beginning
            index = len(self) + index
        if index < 0 or index >= len(self):
            raise IndexError 
        
        param = self.data[index]
        
        if param == None:
            return 'null'
            
        if type(param) is dict:
            if 'type' in param and 'value' in param and IsParamTypeWord(param['type']):
                return list(TypeToWord.keys())[list(TypeToWord.values()).index(param['type'])]
            else:
                raise KlAkParamTypeError('Unexpected type-like word <' + param['type'] + '> in params value')

        builtin_type_name = type(param).__name__  # builtin types such as 'str', 'int', 'bool' and 'list'
        if builtin_type_name == 'str':
            return 'paramString'
        if builtin_type_name == 'int':
            return 'paramInt'
        if builtin_type_name == 'bool':
            return 'paramBool'
        if builtin_type_name == 'list':
            return 'paramArray'
            
        raise KlAkParamTypeError('Unexpected type <' + builtin_type_name + '> in params value')
                
    def GetValue(self, index):
        """ Returns a value in params structure (i.e. str, int, bool values or dict {'type': 'long', 'value': '123'}) for given index. 
            Used this method for composing other params object using values from this array.
            If you need a typed value, such as 123 number in the above case, use [] operator instead. """
        if not type(index) is int:
            raise TypeError
        if index < 0:  # treat as count backwards from end to beginning
            index = len(self) + index
        if index < 0 or index >= len(self):
            raise IndexError 
        
        return self.data[index]
        
    def __getitem__(self, index):
        """ Override [] operator, returns typed value for given index """
        if not type(index) is int:
            raise TypeError
        if index < 0:  # treat as count backwards from end to beginning
            index = len(self) + index
        if index < 0 or index >= len(self):
            raise IndexError 
        
        return extractParamValue(self.data[index])
        
    # to emulate list completely you need override the following: __getslice__, __setslice__ and __delslice__
       
####

class KlAkParams:
    """ KlAkParams represents Params container type that is essential part of KLOAPI.
    Params container is used as method parameters, return values, output parameters and error description in KLOAPI calls. 
    KlAkParams is based on python builtin dict type, offers additional type checking/converting (helpful util as KLOAPI use strong typing)
    and offers formatted output for best readability of KSC objects """

    prefix_param = '+---'
    prefix_indent = '|   '
    prefix_indent_last = '    '

    def __init__(self, data = {}):
        self.data = {}
        if data == None:
            return
        if type(data) is KlAkParams:
            self.data = copy.deepcopy(data.data)
            return
        if not type(data) is dict:
            raise KlAkParamTypeError('KlAkParams is dict wrapper, no other datatypes are allowed for initialization KlAkParams object')   
        if IsParamType(data):
            raise KlAkParamTypeError('KlAkParams does not accept unnamed params contents in constructor')   
        for key, value in data.items():
            if IsParamType(value):
                if type(value) in [KlAkArray, KlAkParams]:
                    self.data[key] = value.data
                else:
                    self.data[key] = value
            else:
                wrapped_value = paramXXX(value)
                if wrapped_value == None:
                    raise KlAkParamTypeError('KlAkParams does not support datatype ' + str(type(value)) + ' used for key <' + key + '>. Please use paramInt/paramLong/paramStr or other converters to construct params values')
                self.data[key] = wrapped_value
                

    def __repr__(self):
        return repr(self.data)    

    def __len__(self):
        return len(self.data)
        
    def __PrintParamsRaw(data, indent='', name='', is_last = True):
        """ Prints params object in terms of Python data types in tree view. For printing plain text instead of tree view you can use >> print(self.data) """  
        result = indent + KlAkParams.prefix_param + name + ' = ' + str(type(data)) + ' '
        if type(data) is dict:
            result += '\n'          
            for i, key in enumerate(data):
                new_indent = indent + (lambda: KlAkParams.prefix_indent_last if is_last else KlAkParams.prefix_indent)()
                result += KlAkParams.__PrintParamsRaw(data[key], new_indent, key, i == len(data) - 1)
        elif type(data) is list: 
            result += '\n'
            for i, listelem in enumerate(data):
                new_indent = indent + (lambda: KlAkParams.prefix_indent_last if is_last else KlAkParams.prefix_indent)()
                result += KlAkParams.__PrintParamsRaw(listelem, new_indent, str(i), i == len(data) - 1)
        elif type(data) in [str, int, bool, float]: 
            result += str(data) + '\n'
        elif data == None:
            result += ' null\n'  
        else:
            result += 'UNEXPECTED VALUE!'
        return result

    def __PrintParamsParsed(data, indent='', is_last = True):
        """ Prints params object in terms of KLOAPI types """  
        result = ''
        
        if type(data) is KlAkParams:
            for i, key in enumerate(data.GetNames()):
                cur_type = data.GetType(key)
                cur_value = data[key]
                new_indent = indent + (lambda: KlAkParams.prefix_indent_last if is_last else KlAkParams.prefix_indent)()
                result += new_indent + KlAkParams.prefix_param + key + ' = (' + cur_type + ') '
                if cur_type in ['paramParams', 'paramArray']:
                    result += '\n' + KlAkParams.__PrintParamsParsed(cur_value, new_indent, i == len(data.GetNames()) - 1)
                else:
                    result += str(cur_value) + '\n'
        elif type(data) is KlAkArray:        
            for i in range(len(data)):
                cur_type = data.GetType(i)
                cur_value = data[i]
                new_indent = indent + (lambda: KlAkParams.prefix_indent_last if is_last else KlAkParams.prefix_indent)()
                result += new_indent + KlAkParams.prefix_param + str(i) + ' = (' + cur_type + ') '
                if cur_type in ['paramParams', 'paramArray']:
                    result += '\n' + KlAkParams.__PrintParamsParsed(cur_value, new_indent, i == len(data) - 1)
                else:
                    result += str(cur_value) + '\n'
                 
        return result       
        
    def PrintRaw(self):
        """ Prints params object in terms of Python data types in tree view. For printing plain text instead of tree view you can use >> print(self.data) """  
        return KlAkParams.__PrintParamsRaw(self.data, "")

    def PrintParsed(self):
        """ Prints params object in terms of KLOAPI types """  
        return KlAkParams.prefix_param + ' (params)\n' + KlAkParams.__PrintParamsParsed(self, "")

    def __str__(self):
        return self.PrintParsed()
        
    def __contains__(self, name):
        return name in self.data
        
    def GetNames(self):
        """ Returns all the keys in params object in terms of KLOAPI """
        return self.data.keys()
        # TODO: smth about __keytransform__
    
    def GetValue(self, name):    
        """ Returns value in params structure (i.e. str, int, bool values or dict {'type': 'long', 'value': '123'})
            Used this method for composing other KlAkParams/KlAkArray object using values from this object.
            If you need a typed value, such as 123 number in the above case, use [] operator instead. """
        if not name in self.data:
            raise KlAkParamTypeError('KlAkParams object does not contain <'+ name + '> section')
       
        return self.data[name]
        
    def __getitem__(self, name):
        """ Returns typed value (int, string, bool, float, datetime, date, bytes, KlAkParams or KlAkArray) of element of params (i.e. returns int 123 for params which contents is {'type': 'long',  'value': 123}. """
        if not name in self.data:
            raise KlAkParamTypeError('KlAkParams object does not contain <'+ name + '> section')
            
        return extractParamValue(self.data[name])
        
    def __setitem__(self, name, value):
        """ Adds a value, value type is defined automatically from value type. 
        ATTENTION! Can not distinguish int / long and float / double datatypes. To add paramLong or paramFloat, please call AddLong and AddFloat methods explicitly """
        self.data.update({name: paramXXX(value)}) 
    
    def GetType(self, name):
        """ Returns type of element of params (i.e. 'paramString', 'paramsLong', 'paramParams', etc. """
        if not name in self.data:
            raise KlAkParamTypeError('KlAkParams object does not contain <'+ name + '> section')
        
        param = self.data[name]
            
        if type(param) is dict:
            if 'type' in param and 'value' in param and IsParamTypeWord(param['type']):
                return list(TypeToWord.keys())[list(TypeToWord.values()).index(param['type'])]
            else:
                raise KlAkParamTypeError('Unexpected type-like word <' + param['type'] + '> in params value')

        builtin_type_name = type(param).__name__  # builtin types such as 'str', 'int', 'bool' and 'list'
        if builtin_type_name == 'str':
            return 'paramString'
        if builtin_type_name == 'int':
            return 'paramInt'
        if builtin_type_name == 'bool':
            return 'paramBool'
        if builtin_type_name == 'list':
            return 'paramArray'
            
        raise KlAkParamTypeError('Unexpected type <' + builtin_type_name + '> in params value')
        
    def AddString(self, name, value):
        """ Add a value of type str, treat as paramString value """
        self.data.update({name: paramString(value)})
        
    def AddBool(self, name, value):
        """ Add a value of type bool, treat as paramBool value """
        self.data.update({name: paramBool(value)})       
       
    def AddInt(self, name, value):
        """ Add a value of type int, treat as paramInt value """
        self.data.update({name: paramInt(value)})    
        
    def AddLong(self, name, value):
        """ Add a value of type int, contains paramLong-wrapper inside """
        self.data.update({name: paramLong(value)})  
       
    def AddDateTime(self, name, value):
        """ Add a value of type datetime or str (in case of str performs check for datetime format, otherwise transforms data to string of proper format) and contains paramDateTime-wrapper inside """
        self.data.update({name: paramDateTime(value)})   
        
    def AddDate(self, name, value):
        """ Add a value of type date or datetime or str (in case of str performs check for date format, otherwise transforms data to string of proper format) and contains paramDate-wrapper inside """
        self.data.update({name: paramDate(value)})   
        
    def AddBinary(self, name, value):
        """ Add a value of type str or bytes (in case of bytes performs base64 encoding) and contains paramBinary-wrapper inside """
        self.data.update({name: paramBinary(value)})   
    
    def AddFloat(self, name, value):
        """ Add a value of type float, contains paramFloat-wrapper inside """
        self.data.update({name: paramFloat(value)})    
    
    def AddDouble(self, name, value):
        """ Add a value of type float, treated as double (builtin float type in python corresponds to double in C\Java) contains paramDoule-wrapper inside """
        self.data.update({name: paramDouble(value)})    
        
    def AddArray(self, name, value):
        """ Add a value of type KlAkArray or list which contents corresponds to paramParams structure """
        if not IsParamType(value):
            value_wrapped = paramXXX(value)
            if value_wrapped == None:
                raise KlAkParamTypeError('KlAkParams does not support given datatype for paramArray section <' + name + '>. Please use paramArray converter or KlAkArray constructor to construct array section')
            else:
                self.data.update({name: paramArray(value)})
        elif type(value) in [KlAkArray, KlAkParams]:
            self.data.update({name: paramArray(value.data)})
        else:
            self.data.update({name: paramArray(value)})
        
    def AddParams(self, name, value):
        """ Add a value of type KlAkParams or dict which corresponds to params (not paramParams) structure: contains paramParams-wrapper inside """
        if not type(value) in [dict, KlAkParams]:
            raise KlAkParamTypeError('KlAkParams does not support given datatype for paramParams section <' + name + '>. Please use dict or KlAkParams object to construct paramParams section')
        
        self.data.update({name: paramXXX(value)})

    def Add(self, name, value):   
        """ Add a value that was retrieved from another KlAkParams/KlAkArray object with GetValue(...) method or raw dict which contents corresponds to paramString/paramsInt/.../paramArray/paramParams structure """    
        if IsParamType(value):
            self.data.update({name: value}) 
        else:
            raise KlAkParamTypeError('KlAkParams cannot accept value with inproper structure for section <' + name + '>.')
            
    def __delitem__(self, name):
        del self.data[name]


class KlAkParamsEncoder(JSONEncoder):
    """ Implements KlAkParams class serialization to JSON """
    def default(self, o):
        if type(o) in [KlAkParams, KlAkArray]:
            return o.data
        elif type(o) is bytes:
            return binToStr(o)
        return JSONEncoder.default(self, o)
        