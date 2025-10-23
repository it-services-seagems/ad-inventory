#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAk package to connect server with different authentication methods
KlAk package is a wrapper library for interacting Kaspersky Security Center (aka KSC) server with KSC Open API
For detailed KSC Open API protocol description please refer to KLOAPI documentation pages
"""

import sys
import os
import argparse
import socket
import getpass
from urllib.parse import urlparse
from .Params import KlAkParams, KlAkArray, paramParams
from .AdmServer import KlAkAdmServer
from .Error import KlAkError, KlAkResponseError
from .ServerHierarchy import KlAkServerHierarchy
from .CgwHelper import KlAkCgwHelper
from .GatewayConnection import KlAkGatewayConnection    
from .HostGroup import KlAkHostGroup
from .ChunkAccessor import KlAkChunkAccessor
from .NagHstCtl import KlAkNagHstCtl

def GetSlaveServerByName(main_server, slave_name):
    """ Acquire information about secondary servers in Managed devices group and returns information about first of them """
    hostGroup = KlAkHostGroup(main_server)
    nRootGroupID = hostGroup.GroupIdGroups().RetVal()
    
    server_hrch = KlAkServerHierarchy(main_server)
    arrChildren = server_hrch.GetChildServers(nRootGroupID).RetVal()
    if arrChildren == None or len(arrChildren) < 1:
        print('There are no child servers to connect')
    else:
        for childServer in arrChildren:
            if childServer["KLSRVH_SRV_DN"] == slave_name:
                return childServer
        
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
    
def _ConnectBasicAuth(server_url, user_account, password, domain = '', internal_user_flag = True, verify = True, vserver = ''):
    """ Connect KSC server using basic authentication"""
    print ('Connecting with basic authentication to KSC server:', server_url, (lambda:'virtual server ' + vserver if vserver != '' else '')(), 'under account', user_account)
        
    server = KlAkAdmServer.Create(server_url, user_account, password, domain, internal_user_flag, verify, vserver)
    if server.connected:
        print ('KSC server connected successfully!')
    else:
        print ('KSC server connection failed')
    
    return server
    
def _ConnectNTLMAuth(server_url, verify = True, vserver = ''):
    """ Connect KSC server using basic authentication"""
    print ('Connecting with NTLM authentication to KSC server:', server_url, (lambda:'virtual server ' + vserver if vserver != '' else '')())
        
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

def PrepareSlaveGatewayConnection(server_main, server_parent_on_hierarchy = None, slave_name = "", arrLocation = []):
    """ Prepares token for gateway connection to slave server; see 'Creating gateway connections' section in KLOAPI documentation
        arrLocation is updated with slave server location, can be used in creating chain of locations down by hierarchy """
    if server_parent_on_hierarchy == None:
        server_parent_on_hierarchy = server_main
        
    childServer = GetSlaveServerByName(server_parent_on_hierarchy, slave_name)
    if childServer == None:
        raise KlAkError('Cannot find slave server to connect')
    
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
    
def PrepareSlaveNagentGatewayConnection(server_main, slave_name, nagent_fqdn, arrLocation = [], verify = True):
    """ Prepares token for gateway connection to slave's nagent; see 'Creating gateway connections' section in KLOAPI documentation """
   
    # step 1 : get slave server location, update locations array
    token_on_slave = PrepareSlaveGatewayConnection(server_main, server_main, slave_name, arrLocation)  # arrLocation filled with slave server address
    if token_on_slave == None:
        return
    
    # here we can go down by hierarchy if needed:
    # server_slave = KlAkAdmServer.CreateGateway(server_main.URL(), token_on_slave)   # 1-st level on hierarchy
    # token_on_slave_on_slave = PrepareSlaveGatewayConnection(server_main, server_slave, slave_name, arrLocation)
    # server_slave_on_slave = KlAkAdmServer.CreateGateway(server_main.URL(), token_on_slave_on_slave)  # 2-nd level on hierarchy
    # and so far
    
    # step 2 : get nagent location on slave server, update locations array
    server_slave = KlAkAdmServer.CreateGateway(server_main.URL(), token_on_slave, verify = (lambda: verify if verify != None else False)())   
    
    # step 3: prepare gateway connection to main server with locations array built on previous step
    token_on_nagent_on_slave = PrepareNagentGatewayConnection(server_main, server_slave, GetHostNameByHostFQDN(server_slave, nagent_fqdn), arrLocation)  

    # use token for further gateway connection to nagent on slave server
    return token_on_nagent_on_slave     

def _ConnectNagentGatewayAuth(server_url, gw_token, verify = True, silent = False):
    """ Connect nagent using gateway connection. 
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
        

def _ConnectServerGatewayAuth(server_url, gw_token, verify = True, silent = False):
    """ Connect slave server using gateway connection. 
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
       
def Connect(server_url = '', server_port = 13299, vserver = '', verify = '', sUser = '', sPassword = '', strNagentFQDN = None, strSlaveServerName = None, silent = False):
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
    
    # credentials for basic auth; if empty, NTLM is used on Windows platform
    user = sUser
    password = sPassword
    if (sUser != None and sUser != '') and (password == None or password == ''):
        password = getpass.getpass(prompt='Input password: ')
    
    # connecting
    if user is not None:
        server_main = _ConnectBasicAuth(server_url, user, password, internal_user_flag = True, verify = verify, vserver = vserver)
    else:
        server_main = _ConnectNTLMAuth(server_url, verify = verify, vserver = vserver)
    
    bBasicAuth                 = (strSlaveServerName == None) and (strNagentFQDN == None)
    bGatewayNagentAuth         = (strSlaveServerName == None) and (strNagentFQDN != None)
    bGatewaySlaveServerAuth    = (strSlaveServerName != None) and (strNagentFQDN == None)
    bGatewayNagentOnServerAuth = (strSlaveServerName != None) and (strNagentFQDN != None)
    
    server = None
    if bBasicAuth:
        server = server_main
    elif bGatewayNagentAuth:
        print ('-- Prepare nagent gateway connection --')
        token = PrepareNagentGatewayConnection(server_main, wsHostName = GetHostNameByHostFQDN(server_main, strNagentFQDN) ) # prepare token to connect to nagent on current device; or use wanted device fqdn here
        server = _ConnectNagentGatewayAuth(server_url, token, verify = verify, silent = silent)
    elif bGatewaySlaveServerAuth:
        print ('-- Prepare slave gateway connection --')
        token = PrepareSlaveGatewayConnection(server_main, server_main, strSlaveServerName) # prepare token to connect to slave
        server = _ConnectServerGatewayAuth(server_url, token, verify = verify, silent = silent)
    elif bGatewayNagentOnServerAuth:
        print ('-- Prepare gateway connection to nagent on slave --')
        token = PrepareSlaveNagentGatewayConnection(server_main, strSlaveServerName, strNagentFQDN, verify = verify)  # prepare token to connect to nagent on first machine in Managed devices group on first slave server in main server's Managed devices group
        server = _ConnectNagentGatewayAuth(server_url, token, verify = verify, silent = silent)

    return server
    
def AddConnectionArgs(parser):
    """ Command line argumets description.
        Samples of command line that can be parsed here:
        '' (empty strig) - connection with basic auth to main KSC server installed on current machine with default port under account 'klakoapi_test', password is asked interactively
        '-address "https://ksc.example.com" -port 12100 -user test_operator -password test1234!' - connection to server installed on 'https://ksc.example.com:12100' under account 'test_operator' with password 'test1234!'
        '-slave test_slave -user test_operator -password test1234!' - connection to slave server named 'test_slave', whose parent is KSC server installed on current machine. Account 'test_operator' with password 'test1234!' is used.
        '-vserver v1 test_slave -user test_operator' - connection to virtual server named 'v1', whose parent is KSC server installed on current machine. Account 'test_operator' is used, password is asked interactively.
        '-nagent machine.domain.com' - connection to nagent installed on machine 'machine.domain.com' connected to KSC server installed on curret machine under account 'klakoapi_test'
        '-slave test_slave -nagent machine_on_slave.domain.com' - connection to nagent installed on machine 'machine_on_slave.domain.com' connected to slave named 'test_slave', whose parent is KSC server installed on current machine. Account 'klakoapi_test' is used
        """
    group_address = parser.add_argument_group()
    group_address.add_argument('-address', action='store', help='(optional) address where main KSC server is located, for example "https://ksc.example.com". If no -address option is used, suppose KSC server is installed on current machine')
    group_address.add_argument('-port', type=int, action='store', help='(optional) KSC server port, by default port 13299 is used')
    group_address.add_argument('-vserver', action='store', default = '', help='(optional) KSC virtual server name. If absent, connect to main server')
    group_address.add_argument('-verify', action='store', help='(optional) path to SSL certificate of main KSC server. If module runs on the machine where KSC server is installed, use "-verify C:\\ProgramData\\KasperskyLab\\adminkit\\1093\\cert\\klserver.cer"')
    group_address.add_argument('-user', action='store', help='(optional) internal account for basic auth on main KSC server and for preparation steps for gateway connection')
    group_address.add_argument('-password', action='store', help='(optional) password to account for basic auth on main KSC server and for preparation steps for gateway connection. If absent, password is asked interactively')

    group_address.add_argument('-slave', metavar='SLAVE_NAME', action='store', help='gateway authentication to slave server with given name. If -slave and -nagent arguments are both given, connection is performed to nagent on slave server. If neither -slave nor -nagent are given, connection is performed to main server.')
    group_address.add_argument('-nagent', metavar='NAGENT_FQDN', action='store', help='gateway authentication to nagent on a machine with given FQDN. If -slave and -nagent arguments are both given, connection is performed to nagent on slave server. If neither -slave nor -nagent are given, connection is performed to main server.')
             
    return

def ConnectFromCmdline(args, silent=True):
    """ Creates connection using command line argumens that were previously added with AddConnectionArgs  """
    return Connect(args.address, args.port, args.vserver, args.verify, args.user, args.password, args.nagent, args.slave, silent)     

def main():
    """ Depending on command line arguments this module shows KSC connection with different authentication methods.
    Address of KSC server is optional argument, and if not stated then current machine FQDN is used (supposed tests are run on machine where KSC server is installed)    
    Samples of usage:
    
    >> ConnectionHelper.py -address "https://ksc.example.com" -port 12100 -user test_operator -password test1234!
    Connecting with basic authentication to KSC server: https://ksc.example.com:12100 under account test_operator
    KSC server connected successfully!
    
    >> ConnectionHelper.py -verify C:\ProgramData\KasperskyLab\adminkit\1093\cert\klserver.cer
    Connection with NTLM authentication to KSC server: https://currentmachine.currentdomain.com:13299
    KSC server connected successfully!

    >> ConnectionHelper.py -user no_such_user -password test1234! -verify C:\ProgramData\KasperskyLab\adminkit\1093\cert\klserver.cer
    Connection with basic authentication to KSC server: https://currentmachine.currentdomain.com:13299 under account no_such_user
    Traceback (most recent call last):
    ...
    KlAkOAPI.Error.KlAkResponseError: Authentication failure
    
    >> ConnectionHelper.py -gwslave test_slave -verify C:\ProgramData\KasperskyLab\adminkit\1093\cert\klserver.cer
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
    AddConnectionArgs(parser)
    args = parser.parse_args()
   
    #KSC connection
    server = ConnectFromCmdline(args)   

    
if __name__ == '__main__':
    main()