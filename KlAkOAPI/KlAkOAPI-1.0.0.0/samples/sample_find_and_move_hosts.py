# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to find host by query and move it to a new group"""

import socket
import datetime
import time
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.AsyncActionStateChecker import KlAkAsyncActionStateChecker
from KlAkOAPI.Base import MillisecondsToSeconds

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
    
def FindHostsByQueryString(server, strQueryString):
    print('Query string: ' + strQueryString)

    strAccessor = KlAkHostGroup(server).FindHosts(strQueryString, ['KLHST_WKS_HOSTNAME', 'KLHST_WKS_DN'], [], {'KLGRP_FIND_FROM_CUR_VS_ONLY': True}, lMaxLifeTime = 60 * 60).OutPar('strAccessor')
    
    nStart = 0
    nStep = 100
    oChunkAccessor = KlAkChunkAccessor (server)    
    nCount = oChunkAccessor.GetItemsCount(strAccessor).RetVal()
    print('Found hosts for query string:', nCount)
    
    oResult = KlAkArray([])
    while nStart < nCount:
        oChunk = oChunkAccessor.GetItemsChunk(strAccessor, nStart, nStep)
        oHosts = oChunk.OutPar('pChunk')['KLCSP_ITERATOR_ARRAY']
        for oObj in oHosts:
            print('Found host: ' + oObj['KLHST_WKS_DN'])
            oResult.Add(oObj.GetValue('KLHST_WKS_HOSTNAME'))
        nStart += nStep    

    return oResult

    
def main():
    """ This sample shows how you can find and move hosts """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    # create new group and move hosts there
    oHostGroup = KlAkHostGroup(server)
    strGroupName = 'TestGroup'

    # create new group
    nRootGroupID = oHostGroup.GroupIdGroups().RetVal()
    nDstGroupId = oHostGroup.AddGroup({'name': strGroupName, 'parentId': nRootGroupID}).RetVal()

    # find hosts by fqdn
    oFoundHosts = FindHostsByQueryString(server, '(&(KLHST_WKS_GROUPID <> ' + str(nDstGroupId) + ' )(KLHST_WKS_FQDN=\"' + socket.getfqdn() + '\"))')   
    
    # move hosts in group created earlier
    oHostGroup.MoveHostsToGroup(nDstGroupId, oFoundHosts)
    
if __name__ == '__main__':
    main()