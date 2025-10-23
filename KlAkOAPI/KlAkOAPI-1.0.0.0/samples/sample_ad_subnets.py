# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create ip subnets based on AD Site and Services"""

import socket
import win32com.client
import ctypes
import datetime
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams, paramInt
from KlAkOAPI.Error import KlAkError
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.ScanDiapasons import KlAkScanDiapasons
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
 
def GetServer():
    """Connects to KSC server"""
    # server details - connect to server installed on current machine, use default port
    server_address = socket.getfqdn()
    server_port = 13299
    server_url = 'https://' + server_address + ':' + str(server_port)

    if platform == "win32":
        username = None # for Windows use NTLM by default
        password = None
    else:
        username = 'klakoapi_test' # for other platform use basic auth, user should be created on KSC server in advance
        password = 'test1234!'        
    
    SSLVerifyCert = 'C:\\ProgramData\\KasperskyLab\\adminkit\\1093\\cert\\klserver.cer'

    # create server object
    server = KlAkAdmServer.Create(server_url, username, password, verify = SSLVerifyCert)
    
    return server
 
def GetDefaultNamingContext():
    # returns default AD naming context   
    oRootDSE = win32com.client.GetObject('LDAP://RootDSE')
    strDefaultNamingContext = oRootDSE.Get('defaultNamingContext')
    print("DefaultNamingContext is " + strDefaultNamingContext)
    return strDefaultNamingContext

def DeleteAllSubnets(server, oScanDiapasons):
    strAccessor = oScanDiapasons.GetDiapasons(['KLDPNS_ID'], 60 * 60 * 3).RetVal()

    nStart = 0
    nStep = 100
    oChunkAccessor = KlAkChunkAccessor(server)
    
    nCount = oChunkAccessor.GetItemsCount(strAccessor).RetVal()
    while nStart < nCount:
        oChunk = oChunkAccessor.GetItemsChunk(strAccessor, nStart, nStep)
        oDiapasons = oChunk.OutPar('pChunk')['KLCSP_ITERATOR_ARRAY']
        for oObj in oDiapasons:
            nID = oObj['KLDPNS_ID']
            print('ID to delete is', nID)
            oScanDiapasons.RemoveDiapason(nID)
        nStart += nStep    
    
def iptoint(ip):
    return int.from_bytes(socket.inet_aton(ip), byteorder='little')

def main():
    """ This sample shows how you can create ip subnets based on AD Site and Services """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()
    
    strDefaultNamingContext = GetDefaultNamingContext()
    
    oScanDiapasons = KlAkScanDiapasons(server)
    
    # delete all existing subnets if needed
    DeleteAllSubnets(server, oScanDiapasons)
    
    oRoot = win32com.client.GetObject('LDAP://cn=Subnets,cn=Sites,cn=Configuration,' + strDefaultNamingContext)
    print(oRoot.distinguishedName)
    
    strPartOfName = 'MyTestSubnet'

    i = 0
    for oObj in oRoot:
        print(oObj.Name)
        print('Added diapason', oObj.cn)
        oPars = KlAkParams({})
        oPars.AddString('KLDPNS_DN', strPartOfName + " - " + oObj.cn)
        vecStrings = oObj.cn.split('/')
        nMaskBits = int(vecStrings[1])
        nMask = socket.htonl((0xffffffff << (32 - nMaskBits)) & 0xffffffff)
        nMask = ctypes.c_long(nMask).value   # transform to c-type "signed long"
        nIp = iptoint(vecStrings[0]) & nMask
        nIp = ctypes.c_long(nIp).value       # transform to c-type "signed long"
        oPars.AddArray('KLDPNS_ILS', [paramParams({'KLDPNS_IL_ISSUBNET': True, 'KLDPNS_IL_MASKORLOW': paramInt(nMask), 'KLDPNS_IL_SUBNETORHI': paramInt(nIp)})])
        oPars.AddInt('KLDPNS_LF', 3600*8)
        oPars.AddBool('KLDPNS_ScanEnabled', False)  # disable network scan for  subnet
        print('\n', oPars)
        
        try:
            idDiapason = oScanDiapasons.AddDiapason(oPars).RetVal()
            print(idDiapason)
        except KlAkError as err :
            print (err.data)
            raise
        
if __name__ == '__main__':
    main()