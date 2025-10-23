# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to set update agents"""

import socket
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams, paramLong
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.UaControl import KlAkUaControl

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
    
def SetUpdateAgents(server):
    #for example, register all hosts in selected group (not in subgroups) as Update Agents
    oHostGroup = KlAkHostGroup(server)
    oUpdAgents = KlAkUaControl(server)

    if oUpdAgents.GetAssignUasAutomatically().RetVal() == True:
        print('Update agents are now set automatically. Change this settings to allow this module demonstration of work with update agents')
        oUpdAgents.SetAssignUasAutomatically(False)
    
    #select root group
    lGroup2Process = oHostGroup.GroupIdGroups().RetVal()

    #all hosts with nagent that have lGroup2Process as parent group
    strAccessor = oHostGroup.FindHosts( '(&(KLHST_INSTANCEID <> \"\")(KLHST_WKS_GROUPID = ' + str(lGroup2Process) + '))', ['KLHST_WKS_HOSTNAME', 'KLHST_WKS_DN'], [], {'KLGRP_FIND_FROM_CUR_VS_ONLY': True}, lMaxLifeTime = 60 * 60 * 3).OutPar('strAccessor')
    
    nStart = 0
    nStep = 100
    oChunkAccessor = KlAkChunkAccessor (server)    
    nCount = oChunkAccessor.GetItemsCount(strAccessor).RetVal()
    print("Found hosts count:", nCount)
    
    while nStart < nCount:
        oChunk = oChunkAccessor.GetItemsChunk(strAccessor, nStart, nStep)
        parHosts = oChunk.OutPar('pChunk')['KLCSP_ITERATOR_ARRAY']
        for oObj in parHosts:
            print('Found host: ' + oObj['KLHST_WKS_DN'])
            
            #register found host as update agent       
            pUaInfo = KlAkParams({})
            pUaInfo.Add('UaHostId', oObj.GetValue('KLHST_WKS_HOSTNAME'))            
            pUaScope = KlAkParams({'ScopeGroups': [ paramParams({'ScopeId': paramLong(lGroup2Process), 'ScopeName': 'test scope'}) ]})
            pUaInfo.AddParams('UaScope', pUaScope)
            
            oUpdAgents.RegisterUpdateAgent(pUaInfo)
        nStart += nStep 


def main():
    """ This sample shows how you can set update agents """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    SetUpdateAgents(server)

    
if __name__ == '__main__':
    main()