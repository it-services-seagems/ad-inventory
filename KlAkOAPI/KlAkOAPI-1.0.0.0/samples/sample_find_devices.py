# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to find devices"""

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
        pRecords = oSrvView.GetRecordRange(wstrIteratorId, iStart, iStep).OutPar('pRecords')
        for i, oObj in enumerate(pRecords['KLCSP_ITERATOR_ARRAY']):
            print ('Device ' + str(i + 1) + ':')
            if 'Dev_Model' in oObj:
                print('\tDevice model: ', oObj['Dev_Model'])
            if 'Dev_OS' in oObj:
                print('\tDevice OS: ', oObj['Dev_OS'])
            if 'Dev_FrName' in oObj:
                print('\tDevice friendly name: ', oObj['Dev_FrName'])
            if 'Dev_IMEI' in oObj:
                print('\tDevice IMEI: ', oObj['Dev_IMEI'])
            if 'Dev_PhNumber' in oObj:
                print('\tDevice phone number: ', oObj['Dev_PhNumber'])
        iStart += iStep

    oSrvView.ReleaseIterator(wstrIteratorId)


def main():
    """ This sample shows how you can find devices """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oSrvView = KlAkSrvView(server)	
    
    wstrIteratorId = oSrvView.ResetIterator('UmdmAllDevices', '', ['Dev_Model',  'Dev_OS', 'Dev_FrName', 'Dev_IMEI', 'Dev_PhNumber'], [], {}, lifetimeSec = 60 * 60 * 3).OutPar('wstrIteratorId')
    
    Enumerate(oSrvView, wstrIteratorId)

    
if __name__ == '__main__':
    main()