# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to find incidents"""

import socket
from sys import platform
from KlAkOAPI.Params import KlAkParams
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
 
def FindHostIncidents(server, oHostGroup, strFilter):
    print('Filter string: ' + strFilter)

    strAccessor = oHostGroup.FindIncidents(strFilter, ['KLINCDT_ID', 'KLINCDT_SEVERITY', 'KLINCDT_ADDED', 'KLINCDT_BODY', 'KLINCDT_IS_HANDLED', 'KLHST_WKS_HOSTNAME', 'GNRL_EXTRA_PARAMS'], [], lMaxLifeTime = 60 * 60).OutPar('strAccessor')
    
    oChunkAccessor = KlAkChunkAccessor(server)    
    lRecords = oChunkAccessor.GetItemsCount(strAccessor).RetVal()
    print('Found', lRecords, 'host incidents')

    nStart = 0
    nStep = 200
    oResult = []
    while nStart < lRecords:
        oChunk = oChunkAccessor.GetItemsChunk(strAccessor, nStart, nStep)
        parIncidents = oChunk.OutPar('pChunk')['KLCSP_ITERATOR_ARRAY']
        for oObj in parIncidents:
            print('Found incident: ID =', oObj['KLINCDT_ID'], ', Severity =' , oObj['KLINCDT_SEVERITY'],  ', Added =', oObj['KLINCDT_ADDED'], ', Body =', oObj['KLINCDT_BODY'], ', IsHandled =',  oObj['KLINCDT_IS_HANDLED'], ', Hostname =', oObj['KLHST_WKS_HOSTNAME'])
            if 'GNRL_EXTRA_PARAMS' in oObj:
                print('Custom params: TEST_STRING =', oObj['GNRL_EXTRA_PARAMS']['TEST_STRING'])
                print('Custom params: TEST_INT =', oObj['GNRL_EXTRA_PARAMS']['TEST_INT'])
            oResult.append(oObj['KLINCDT_ID'])
               
        nStart += nStep    

    return oResult

    
def main():
    ''' This sample shows how you can find incidents '''
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oHostGroup = KlAkHostGroup(server)    
    FindHostIncidents(server, oHostGroup, 'KLINCDT_IS_HANDLED=1')

    
if __name__ == '__main__':
    main()