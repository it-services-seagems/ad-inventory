# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create group structure based on cached AD organization units structure"""

import socket
import time
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.SrvView import KlAkSrvView
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.AdHosts import KlAkAdHosts
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
    
def processOU(server, oHostGroup, oAdHosts, nOU, nLevel, oFileds2Return, nGroup):
    wstrIteratorId = oAdHosts.GetChildOUs(nOU, oFileds2Return, lMaxLifeTime = 60 * 60).RetVal()
    
    oChunkAccessor = KlAkChunkAccessor(server)
    nCount = oChunkAccessor.GetItemsCount(wstrIteratorId).RetVal()
    nStart = 0
    nStep = 200
    while nStart < nCount:
        oChunk = oChunkAccessor.GetItemsChunk(wstrIteratorId, nStart, nStep).OutPar('pChunk')

        for oObj in oChunk['KLCSP_ITERATOR_ARRAY']:
            # OU name
            strName = oObj['adhst_idComputer']
            nId = oObj['adhst_id']

            # form indention for logging
            strIndention = '    ' + '  ' * nLevel + '+-'

            # log found OU
            print(strIndention, strName)

            # create group for found OU
            oProps = KlAkParams({'name': strName, 'parentId': nGroup})
            nIdNewGroup = oHostGroup.AddGroup(oProps).RetVal()

            # process subOUs recursively
            processOU(server, oHostGroup, oAdHosts, nId, nLevel+1, oFileds2Return, nIdNewGroup)
        nStart += nStep


    
def main():
    """ This sample shows how you can create group structure based on cached AD organization units structure """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oHostGroup = KlAkHostGroup(server)
    oAdHosts = KlAkAdHosts(server)

    # create new group
    strGroupName = 'TestGroup'
    nRootGroupID = oHostGroup.GroupIdGroups().RetVal()
    lCreatedGroup = oHostGroup.AddGroup({'name': strGroupName, 'parentId': nRootGroupID}).RetVal()

    processOU(server, oHostGroup, oAdHosts, 0, 0, ['adhst_id', 'adhst_idParent', 'adhst_idComputer'], lCreatedGroup)

    
if __name__ == '__main__':
    main()