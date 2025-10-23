# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents sample of usage KlAkOAPI package to perform task on host
"""

import sys
import os
import argparse
import socket
import time
import getpass
from sys import platform
from urllib.parse import urlparse
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams, strToBin
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.Error import KlAkError, KlAkResponseError
from KlAkOAPI.CgwHelper import KlAkCgwHelper
from KlAkOAPI.GatewayConnection import KlAkGatewayConnection    
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.Tasks import KlAkTasks
from KlAkOAPI.HostTasks import KlAkHostTasks
from KlAkOAPI.NagHstCtl import KlAkNagHstCtl

# For basic auth connection you should either state '-user' and '-password' arguments or the following credentials are applied: KSCServerUserAccountDefault / KSCServerUserPasswordDefault
# You should create internal user with these credentials in advance on KSC using WC or MMC console and grant it certain privileges, such as 'Main Administrator' role
# For Windows platform NTLM auth is applied when user and password arguments are omitted
KSCServerUserAccountDefault = 'klakoapi_test'
KSCServerUserPasswordDefault = 'test1234!' 

def GetHostNameByHostFQDN(server, strHostFQDN):
    """ Find (internal) host name by host display name; the returned wsHostName is required for gateway connection to nagent """
    hostGroup = KlAkHostGroup(server)
    hostInfo = hostGroup.FindHosts('(KLHST_WKS_FQDN="' + strHostFQDN + '")', ['KLHST_WKS_HOSTNAME', 'KLHST_WKS_DN', 'name'], [], {'KLGRP_FIND_FROM_CUR_VS_ONLY': True}, 100)
    strAccessor = hostInfo.OutPar('strAccessor')
    
    # get search result (in case of ambiguity first found host is taken)
    chunkAccessor = KlAkChunkAccessor (server)
    items_count = chunkAccessor.GetItemsCount(strAccessor).RetVal()
    if items_count < 1:
        raise KlAkError('no gateway host found by name ' + strHostFQDN)
    res_chunk = chunkAccessor.GetItemsChunk(strAccessor, 0, 1)
    res_array = KlAkParams(res_chunk.OutPar('pChunk'))['KLCSP_ITERATOR_ARRAY']
    res_host = res_array[0]
    wsHostName = res_host['KLHST_WKS_HOSTNAME']

    print('Host for nagent gateway connection is:', strHostFQDN, 'correspondent to device', res_host['KLHST_WKS_DN'], 'in group', res_host['name'])
       
    return wsHostName
    
def GetServer(server_url):
    """Connects to KSC server"""
    # server details - connect to server installed on current machine, use default port

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
    
def PrepareNagentGatewayConnection(server_main, server_parent_on_hierarchy = None, wsHostName = '', arrLocation = []):
    """ Prepares token for gateway connection to nagent; see 'Creating gateway connections' section in KLOAPI documentation
        arrLocation is updated with nagent location, can be used in creating chain of locations down by hierarchy """
    if wsHostName == '':
        raise Exception('no hosts found on server, nothing to demonstrate as nagent gateway connection')
    
    if server_parent_on_hierarchy == None:
        server_parent_on_hierarchy = server_main
        
    # step 1: get nagent location
    cgwHelper = KlAkCgwHelper(server_parent_on_hierarchy)
    nagentLocation = cgwHelper.GetNagentLocation(wsHostName).RetVal()    
    
    # step 2: build locations list
    arrLocation.append(paramParams(nagentLocation))
    
    # step 3: prepare gateway connection to main server with locations array built on previous step
    gatewayConnection = KlAkGatewayConnection(server_main)
    response = gatewayConnection.PrepareGatewayConnection(arrLocation)
    token_on_nagent = response.OutPar('wstrAuthKey')
    
    # use token for further gateway connection to Nagent
    return token_on_nagent  

def ConnectNagentGatewayAuth(server_url, gw_token):
    """ Connect nagent using gateway connection. 
        Token for gateway connection is prepared with PrepareNagentGatewayConnection(...) """
    print ('Main KSC server address:', server_url)
    
    server = KlAkAdmServer.CreateGateway(server_url, gw_token, False)
    
    if server.connected:
        print ('Nagent connected successfully!')
    else:
        print ('Nagent connection failed')
        
    return server

def CreteGatewayToHost(server, server_url, hostId):
       
    # prepare token for gateway auth    
    print ('-- Prepare nagent gateway connection --')
    token = PrepareNagentGatewayConnection(server, wsHostName = hostId) # prepare token to connect to nagent on current device; or use wanted device fqdn here
    server = ConnectNagentGatewayAuth(server_url, token)

    return server
    
def FindHostTask(server, hostId, strDisplayName):
    print('Searching for host task', strDisplayName)

    oHostGroup = KlAkHostGroup(server)
    strSrvObjId = oHostGroup.GetHostTasks(hostId).RetVal()
    
    oHostTasks = KlAkHostTasks(server)

    oHostTasks.ResetTasksIterator(strSrvObjId, '', '', '', '', '')
    pTaskData = None
    while True:
        pTaskData = oHostTasks.GetNextTask(strSrvObjId).OutPar('pTaskData')
        
        if pTaskData == None or len(pTaskData) == 0:
            break
            
        strDN = pTaskData['TASK_INFO_PARAMS']['DisplayName']
        if strDN == strDisplayName:
            print('Task ' + strDN + ' found')
            break
                        
    return pTaskData
    
def StartHostTask(nagHstCtl, taskTsId, strProductName, strProductVersion):
    nagHstCtl.SendTaskAction(strProductName, strProductVersion, taskTsId, 5)
    
def WaitTaskCompletion(nagHstCtl, taskTsId, strProductName, strProductVersion):    
    pFilter = KlAkParams({})
    pFilter.AddParams('klhst-rt-TskInfo', {'klhst-ProductName':strProductName}) 

    n = 0
    bDone = False
    while n < 20 or bDone:
        info = nagHstCtl.GetHostRuntimeInfo(pFilter).RetVal()['klhst-rt-TskInfo'][strProductName]

        bFoundInfo = False
        for taskinfo in KlAkArray(info['klhst-rt-TskArray']):
            if taskinfo['taskStorageId'] == taskTsId:
                print('Current task state:', taskinfo['taskState'])
                
                bFoundInfo = True
                
                if taskinfo['taskState'] != 1: # Not running
                    print('Task completed')
                    bDone = True
                    break
                    
        if not bFoundInfo:
            print('Task completed')
            break
            
        time.sleep(1)
        n += 1
    
def AddArgs(parser):
    group_address = parser.add_argument_group()
    group_address.add_argument('-hostaddress', action='store', help='(optional) address of host where task is located, for example "myworkstation.avp.ru". If no -hostaddress option is used, suppose to use current machine')
    group_address.add_argument('-task', action='store', help='Name of task to execute.')
    return

def main():
    """ Starts host task and waits its completion.   
    Samples of usage:
    
    >> python.exe sample_run_host_task.py -task "Task to execute"
    
    """
 
    #argument parsing
    parser = argparse.ArgumentParser(description='This module provides samples of execution of host\'s task')
    group_auth_type = parser.add_mutually_exclusive_group(required=False)
    AddArgs(parser)
    args = parser.parse_args()

    server_address = socket.getfqdn()
    server_port = 13299
    server_url = 'https://' + server_address + ':' + str(server_port)

    #KSC connection
    server = GetServer(server_url)

    hostaddress = args.hostaddress
    if hostaddress is None:
        hostaddress = socket.getfqdn()
    
    hostId = GetHostNameByHostFQDN(server, hostaddress)
    
    pTaskData = FindHostTask(server, hostId, args.task)

    taskTsId = pTaskData['TASK_UNIQUE_ID']
    strProductName = pTaskData['TASKID_PRODUCT_NAME']
    strProductVersion = pTaskData['TASKID_VERSION']
    
    nagent = CreteGatewayToHost(server, server_url, hostId) 
    nagHstCtl = KlAkNagHstCtl(nagent)

    StartHostTask(nagHstCtl, taskTsId, strProductName, strProductVersion)
    WaitTaskCompletion(nagHstCtl, taskTsId, strProductName, strProductVersion)    

if __name__ == '__main__':
    main()