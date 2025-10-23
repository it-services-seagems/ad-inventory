# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to connect server with different authentication methods
KlAkOAPI package is a wrapper library for interacting Kaspersky Security Center (aka KSC) server with KSC Open API
For detailed description of KSC Open API protocol please refer to KLOAPI documentation pages
"""

import sys
import os
import argparse
import socket
import getpass
from urllib.parse import urlparse
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.Error import KlAkError, KlAkResponseError
from KlAkOAPI.ServerHierarchy import KlAkServerHierarchy
from KlAkOAPI.CgwHelper import KlAkCgwHelper
from KlAkOAPI.GatewayConnection import KlAkGatewayConnection    
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.NagHstCtl import KlAkNagHstCtl

# For basic auth connection you should either state '-user' and '-password' arguments or the following credentials are applied: KSCServerUserAccountDefault / KSCServerUserPasswordDefault
# You should create internal user with these credentials in advance on KSC using WC or MMC console and grant it certain privileges, such as 'Main Administrator' role
# For Windows platform NTLM auth is applied when user and password arguments are omitted
KSCServerUserAccountDefault = 'klakoapi_test'
KSCServerUserPasswordDefault = 'test1234!' 

def GetAnySlaveServer(server):
    """ Acquire information about secondary servers in Managed devices group and returns information about first of them """
    hostGroup = KlAkHostGroup(server)
    nRootGroupID = hostGroup.GroupIdGroups().RetVal()
    
    server_hrch = KlAkServerHierarchy(server)
    arrChildren = server_hrch.GetChildServers(nRootGroupID).RetVal()
    if arrChildren == None or len(arrChildren) < 1:
        print('There are no child servers to connect')
    else:
        return arrChildren[0]
        
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
    
def GetFirstHostName(server):
    """ Find (internal) host name of any device, used for demonstration connection to nagent on slave """
    hostGroup = KlAkHostGroup(server)
    hostInfo = hostGroup.FindHosts('(KLHST_WKS_DN="*")', ['KLHST_WKS_HOSTNAME', 'KLHST_WKS_DN', 'name'], [], {'KLGRP_FIND_FROM_CUR_VS_ONLY': True}, 100)
    strAccessor = hostInfo.OutPar('strAccessor')
    
    # get search result, first found host is taken
    chunkAccessor = KlAkChunkAccessor (server)
    items_count = chunkAccessor.GetItemsCount(strAccessor).RetVal()
    if items_count < 1:
        raise Exception('no hosts found on server, nothing to demonstrate as nagent gateway connection')
        
    res_chunk = chunkAccessor.GetItemsChunk(strAccessor, 0, 1)
    res_array = KlAkParams(res_chunk.OutPar('pChunk'))['KLCSP_ITERATOR_ARRAY']
    res_host = res_array[0]
    
    print('Host for nagent gateway connection is:', res_host['KLHST_WKS_DN'], 'in group', res_host['name'])
    
    return res_host['KLHST_WKS_HOSTNAME']
       
def Sample_KlAkServer_ConnectBasicAuth(server_url, user_account, password, domain = '', internal_user_flag = True, verify = True, vserver = None):
    """ Sample 2a. Connect KSC server using basic authentication"""
    print ('Connecting with basic authentication to KSC server:', server_url + (lambda:' virtual server ' + vserver if vserver != '' else '')(), 'under account', user_account)
        
    server = KlAkAdmServer.Create(server_url, user_account, password, domain, internal_user_flag, verify, vserver)
    if server.connected:
        print ('KSC server connected successfully!')
    else:
        print ('KSC server connection failed')
    
    return server

def Sample_KlAkServer_ConnectNTLMAuth(server_url, verify = True, vserver = None):
    """ Sample 2a. Connect KSC server using basic authentication"""
    print ('Connecting with NTLM authentication to KSC server:', server_url + (lambda:' virtual server ' + vserver if vserver != '' else '')())
        
    server = KlAkAdmServer.CreateNTLM(server_url, verify, vserver)
    if server.connected:
        print ('KSC server connected successfully!')
    else:
        print ('KSC server connection failed')
    
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

def PrepareSlaveGatewayConnection(server_main, server_parent_on_hierarchy = None, arrLocation = []):
    """ Prepares token for gateway connection to slave server; see 'Creating gateway connections' section in KLOAPI documentation
        arrLocation is updated with slave server location, can be used in creating chain of locations down by hierarchy """
    if server_parent_on_hierarchy == None:
        server_parent_on_hierarchy = server_main
        
    childServer = GetAnySlaveServer(server_parent_on_hierarchy)
    if childServer == None:
        return
    
    print('connecting to slave server', childServer['KLSRVH_SRV_DN'], ' in group Managed devices')
    
    # step 1 : get slave server location
    cgwHelper = KlAkCgwHelper(server_parent_on_hierarchy)
    slaveServerLocation = cgwHelper.GetSlaveServerLocation(childServer['KLSRVH_SRV_ID']).RetVal()   

    # step 2: build locations list
    arrLocation.append(paramParams(slaveServerLocation))
 
    # step 3: prepare gateway connection to main server with locations array built on previous step
    gatewayConnection = KlAkGatewayConnection(server_main)
    response = gatewayConnection.PrepareGatewayConnection(arrLocation)
    token_on_slave = response.OutPar('wstrAuthKey')
    
    # use token for further gateway connection to slave server
    return token_on_slave     
    
def PrepareSlaveNagentGatewayConnection(server_main, arrLocation = [], verify = True):
    """ Prepares token for gateway connection to slave's nagent; see 'Creating gateway connections' section in KLOAPI documentation """
   
    # step 1 : get slave server location, update locations array
    token_on_slave = PrepareSlaveGatewayConnection(server_main, server_main, arrLocation)  # arrLocation filled with slave server address
    
    # here we can go down by hierarchy if needed:
    # server_slave = KlAkAdmServer.CreateGateway(server_main.URL(), token_on_slave)   # 1-st level on hierarchy
    # token_on_slave_on_slave = PrepareSlaveGatewayConnection(server_main, server_slave, arrLocation)
    # server_slave_on_slave = KlAkAdmServer.CreateGateway(server_main.URL(), token_on_slave_on_slave)  # 2-nd level on hierarchy
    # and so far
    
    # step 2 : get nagent location on slave server, update locations array
    server_slave = KlAkAdmServer.CreateGateway(server_main.URL(), token_on_slave, verify = (lambda: verify if verify != None else False)())   
    
    # step 3: prepare gateway connection to main server with locations array built on previous step
    token_on_nagent_on_slave = PrepareNagentGatewayConnection(server_main, server_slave, GetFirstHostName(server_slave), arrLocation)    

    # use token for further gateway connection to nagent on slave server
    return token_on_nagent_on_slave     

def Sample_KlAkServer_ConnectNagentGatewayAuth(server_url, gw_token, verify = True, silent = False):
    """ Sample 2c. Connect nagent using gateway connection. 
        Token for gateway connection is prepared with PrepareNagentGatewayConnection(...) or PrepareNagentOnSlaveGatewayConnection(...) """
    print ('Main KSC server address:', server_url)
    
    server = KlAkAdmServer.CreateGateway(server_url, gw_token, verify)
    
    if server.connected:
        print ('Nagent connected successfully!')
        
        if not silent:        
            # ask smth from Nagent for test
            print ('Here you can see HostRuntimeInfo on nagent:')

            nagHstCtl = KlAkNagHstCtl(server)
            pFilter = KlAkParams({})
            pFilter.AddParams('klhst-rt-TskInfo', {'klhst-ProductVersion':''}) 
            print(nagHstCtl.GetHostRuntimeInfo(pFilter).RetVal())
    else:
        print ('Nagent connection failed')
        
    return server
        

def Sample_KlAkServer_ConnectServerGatewayAuth(server_url, gw_token, verify = True, silent = False):
    """ Sample 2d. Connect slave server using gateway connection. 
        Token for gateway connection is prepared with PrepareServerGatewayConnection(...) """
    print ('Main KSC server address:', server_url)
    
    server = KlAkAdmServer.CreateGateway(server_url, gw_token, verify)
    
    if server.connected:
        print ('Slave server connected successfully!')
        
        if not silent:
            # ask smth from slave server for test
            print('Here you can see groups on slave server:')
            
            hostGroup = KlAkHostGroup(server) 
            res = hostGroup.FindGroups('', vecFieldsToReturn=['id', 'name', 'grp_full_name', 'parentId', 'level'], vecFieldsToOrder = [], pParams = {}, lMaxLifeTime=100)
            print('Found ' + str(res.RetVal()) + ' groups on slave server:')    
            strAccessor = res.OutPar('strAccessor')
            
            chunkAccessor = KlAkChunkAccessor (server)
            items_count = chunkAccessor.GetItemsCount(strAccessor).RetVal()
            start = 0
            step = 200
            while start < items_count:        
                res_chunk = chunkAccessor.GetItemsChunk(strAccessor, start, step)
                for group_param in KlAkArray(res_chunk.OutPar('pChunk')['KLCSP_ITERATOR_ARRAY']):
                    print (group_param['grp_full_name'])
                start += step
    else:
        print ('Slave server connection failed')
        
    return server
       
def Connect(server_url = '', server_port = 13299, vserver = None, verify = '', sUser = '', sPassword = '', bBasicAuth = True, bGatewayNagentAuth = False, bGatewayServerAuth = False, bGatewayNagentOnServerAuth = False, silent = False):
    """ Connects to server using one of proposed authentication methods """

    # compose KSC server URL; use fqdn if no explicit url is given
    if server_url == None or server_url == '':
        server_url = socket.getfqdn()    
    
    # compose KSC server URL: use https scheme by default
    o = urlparse(server_url)
    if o.scheme == None or o.scheme == '':
        server_url = 'https://' + o.path
        o = urlparse(server_url)
    
    # compose KSC server URL: if port is part of address, do not alter it: else use server_port argument or default port 13299 if server_port argument is missed
    if o.port == None:
        server_url += ':' + str((lambda: server_port if server_port != None else 13299)())
    
    # SSL certificate: if no cert is given, do not verify connection; for connection to "nagent on slave" only empty or cert path are possible
    if verify == None or verify == '':
        verify = False
        
    if verify == 'no' or verify == 'No' or verify == 'false' or verify == 'False' or verify == 'FALSE' or verify == '0':
        verify = False

    if verify == 'yes' or verify == 'Yes' or verify == 'true' or verify == 'True' or verify == 'TRUE' or verify == '1':
        verify = True   # use certificates from certifi if it is present on the system 
    
    user = sUser
    password = sPassword    
    if sys.platform != 'win32':
        # credentials for basic auth
        user = (lambda: sUser if sUser != None and sUser != '' else KSCServerUserAccountDefault)()
        password = (lambda: sPassword if sPassword != None and sPassword != '' else KSCServerUserPasswordDefault)()

    if (sUser != None and sUser != '') and (password == None or password == ''):
        password = getpass.getpass(prompt='Input password: ')
    
    # connecting
    if user is not None:
        server_main = Sample_KlAkServer_ConnectBasicAuth(server_url, user, password, internal_user_flag = True, verify = verify, vserver = vserver)
    else:
        server_main = Sample_KlAkServer_ConnectNTLMAuth(server_url, verify = verify, vserver = vserver)
    
    if bBasicAuth:
        return server_main

    # prepare token for gateway auth    
    if bGatewayNagentAuth:
        print ('-- Prepare nagent gateway connection --')
        token = PrepareNagentGatewayConnection(server_main, wsHostName = GetHostNameByHostFQDN(server_main, socket.getfqdn()) ) # prepare token to connect to nagent on current device; or use wanted device fqdn here
        server = Sample_KlAkServer_ConnectNagentGatewayAuth(server_url, token, verify = verify, silent = silent)
    elif bGatewayServerAuth:
        print ('-- Prepare slave gateway connection --')
        token = PrepareSlaveGatewayConnection(server_main) # prepare token to connect to first slave in Managed devices group
        server = Sample_KlAkServer_ConnectServerGatewayAuth(server_url, token, verify = verify, silent = silent)
    elif bGatewayNagentOnServerAuth:
        print ('-- Prepare gateway connection to nagent on slave --')
        token = PrepareSlaveNagentGatewayConnection(server_main, verify = verify)  # prepare token to connect to nagent on first machine in Managed devices group on first slave server in main server's Managed devices group
        server = Sample_KlAkServer_ConnectNagentGatewayAuth(server_url, token, verify = verify, silent = silent)

    return server
    
def AddServerAddressArgs(parser):
    group_address = parser.add_argument_group()
    group_address.add_argument('-address', action='store', help='(optional) address where KSC server is located, for example "https://ksc.example.com". If no -address option is used, suppose KSC server is installed on current machine')
    group_address.add_argument('-port', type=int, action='store', help='(optional) KSC server port, by default port 13299 is used')
    group_address.add_argument('-vserver', action='store', default = '', help='(optional) KSC virtual server name. If absent, connect to main server')
    group_address.add_argument('-verify', action='store', help='(optional) path to SSL certificate of KSC server. If module runs on the machine where KSC server is installed, use "-verify C:\\ProgramData\\KasperskyLab\\adminkit\\1093\\cert\\klserver.cer"')
    group_address.add_argument('-user', action='store', help='(optional) internal account for basic auth on KSC server and for preparation steps for gateway connection')
    group_address.add_argument('-password', action='store', help='(optional) password to account for basic auth on KSC server and for preparation steps for gateway connection')
    return

def main():
    """ Depending on command line arguments this module shows KSC connection with different authentication methods.
    Address of KSC server is optional argument, and if not stated then current machine FQDN is used (supposed tests are run on machine where KSC server is installed)    
    Samples of usage:
    
    >> sample_connect.py -b -address "https://ksc.example.com" -port 12100 -user test_operator -password test1234!
    Connecting with basic authentication to KSC server: https://ksc.example.com:12100 under account test_operator
    KSC server connected successfully!
    
    >> sample_connect.py -verify C:\ProgramData\KasperskyLab\adminkit\1093\cert\klserver.cer
    Connection with NTLM authentication to KSC server: https://currentmachine.currentdomain.com:13299
    KSC server connected successfully!

    >> sample_connect.py -user no_such_user -password test1234! -verify C:\ProgramData\KasperskyLab\adminkit\1093\cert\klserver.cer
    Connection with basic authentication to KSC server: https://currentmachine.currentdomain.com:13299 under account no_such_user
    Traceback (most recent call last):
    ...
    KlAkOAPI.Error.KlAkResponseError: Authentication failure
    
    >> sample_connect.py -gwslave -verify C:\ProgramData\KasperskyLab\adminkit\1093\cert\klserver.cer
    Connecting with NTLM authentication to KSC server:  https://currentmachine.currentdomain.com:13299
    KSC server connected successfully!
    -- Prepare slave gateway connection --
    connecting to slave server test_slave  in group Managed devices
    Main KSC server address: https://currentmachine.currentdomain.com:13299
    Slave server connected successfully!
    Here you can see groups on slave server:
    Found 3 groups on slave server:
    Managed devices/
    Managed devices/test slave group/
    Unassigned devices/
    """
 
    #argument parsing
    parser = argparse.ArgumentParser(description='This module provides samples of KSC authorization')
    
    group_auth_type = parser.add_mutually_exclusive_group(required=False)
    group_auth_type.add_argument('-b', action='store_true', help='basic authentication. Account and password are taken from "-user" "-password" arguments. If these arguments are empty, NTLM authentication is used')
    group_auth_type.add_argument('-gwnagent', action='store_true', help='gateway authentication to nagent on current machine')
    group_auth_type.add_argument('-gwslave', action='store_true', help='gateway authentication to slave server; if there are 2 or more slave servers connects to server created first')
    group_auth_type.add_argument('-gwnagentonslave', action='store_true', help='gateway authentication to nagent on slave')
             
    AddServerAddressArgs(parser)
 
    args = parser.parse_args()
    
    if args.b == False and args.gwnagent == False and args.gwslave == False and args.gwnagentonslave == False:
        args.b = True
    
    #KSC connection
    server = Connect(args.address, args.port, args.vserver, args.verify, args.user, args.password, args.b, args.gwnagent, args.gwslave, args.gwnagentonslave)     

    
if __name__ == '__main__':
    main()