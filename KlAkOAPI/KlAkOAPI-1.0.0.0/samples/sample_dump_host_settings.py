# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to view host settings stored in settings storage"""

import socket
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.HostGroup import KlAkHostGroup
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
    
def FindHostsByQueryString(server, oHostGroup, strQueryString):
    print('Query string: ' + strQueryString)
    
    strAccessor = oHostGroup.FindHosts(strQueryString, ['KLHST_WKS_HOSTNAME', 'KLHST_WKS_DN'], [], {'KLGRP_FIND_FROM_CUR_VS_ONLY': True}, lMaxLifeTime = 60 * 60).OutPar('strAccessor')
    
    nStart = 0
    nStep = 100
    oChunkAccessor = KlAkChunkAccessor (server)    
    nCount = oChunkAccessor.GetItemsCount(strAccessor).RetVal()
    print('Found hosts for query string:', nCount)
    oResult = KlAkArray([])
    while nStart < nCount:
        oChunk = oChunkAccessor.GetItemsChunk(strAccessor, nStart, nStep).OutPar('pChunk')
        oHosts = oChunk['KLCSP_ITERATOR_ARRAY']
        for oObj in oHosts:
            print('Found host: ' + oObj['KLHST_WKS_DN'])
            oResult.Add(oObj.GetValue('KLHST_WKS_HOSTNAME'))
        nStart += nStep 

    return oResult    
    
def main():
    """ This sample shows how you can view host settings stored in settings storage """
    print (main.__doc__)

    # connect to KSC server using basic auth by default
    server = GetServer()

    oHostGroup = KlAkHostGroup(server)
    oFoundHosts = FindHostsByQueryString(server, oHostGroup, '(KLHST_WKS_FQDN=\"' + socket.getfqdn() + '\")')

    if len(oFoundHosts) > 0:
        oSSSections = oHostGroup.SS_GetNames(oFoundHosts[0], 'SS_SETTINGS', '1103', '1.0.0.0').RetVal()
        print('Settings dump - Begin')
        for oSection in oSSSections:
            oParData = oHostGroup.SS_Read(oFoundHosts[0], 'SS_SETTINGS', '1103', '1.0.0.0', oSection).RetVal()
            print(oSection)
            print(oParData)
        print('Settings dump - End')
    
if __name__ == '__main__':
    main()