# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to iterate over srvview"""

import socket
import time
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.SrvView import KlAkSrvView


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
    
def Enumerate(oSrvView, wstrIteratorId): 
    iRecordCount = oSrvView.GetRecordCount(wstrIteratorId).RetVal() 
    iStep = 200
    iStart = 0
    while iStart < iRecordCount:
        pRecords = oSrvView.GetRecordRange(wstrIteratorId, iStart, iStart + iStep).OutPar('pRecords')
        for oObj in pRecords['KLCSP_ITERATOR_ARRAY']:
            print('TrusteeId: ', oObj['ul_llTrusteeId'], ', DisplayName: ', oObj['ul_wstrDisplayName'])
        iStart += iStep + 1

    oSrvView.ReleaseIterator(wstrIteratorId)

    
def main():
    ''' This sample shows how you can use srvview '''
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oSrvView = KlAkSrvView(server)	
    oFields2Return = KlAkArray(['ul_llTrusteeId',  'ul_wstrDisplayName'])
    oField2Order = KlAkArray([{'Name': 'ul_llTrusteeId', 'Asc': True}])

    wstrIteratorId = oSrvView.ResetIterator('GlobalUsersListSrvViewName', '', oFields2Return, oField2Order, {}, lifetimeSec = 60 * 60 * 3).OutPar('wstrIteratorId')
    
    Enumerate(oSrvView, wstrIteratorId)

    
if __name__ == '__main__':
    main()