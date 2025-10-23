# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAk package to download network list files via gateway connection to the specified host"""

import sys
import os
import argparse
import socket
import getpass
from urllib.parse import urlparse
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams, strToBin
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.Error import KlAkError, KlAkResponseError
from KlAkOAPI.CgwHelper import KlAkCgwHelper
from KlAkOAPI.GatewayConnection import KlAkGatewayConnection    
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.NagNetworkListApi import KlAkNagNetworkListApi

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
    
def ConnectBasicAuth(server_url, user_account, password, domain = '', internal_user_flag = True, verify = True, vserver = None):
    """ Connect KSC server using basic authentication"""
    print ('Connecting with basic authentication to KSC server:', server_url + (lambda:' virtual server ' + vserver if vserver != '' else '')(), 'under account', user_account)
        
    server = KlAkAdmServer.Create(server_url, user_account, password, domain, internal_user_flag, verify, vserver)
    if server.connected:
        print ('KSC server connected successfully!')
    else:
        print ('KSC server connection failed')
    
    return server

def ConnectNTLMAuth(server_url, verify = True, vserver = None):
    """ Connect KSC server using basic authentication"""
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

def DownloadNlstFile(server, nlstname, nlstfileid, downloadpath):  
    """ Download Nlst file by id to specified 'downloadpath' """
     
    if nlstname is None:
        nlstname = "Backup"
        
    print('Network list name: ', nlstname, ' File id: ', nlstfileid)
    
    NagNetworkList = KlAkNagNetworkListApi(server)
    pFileInfo = NagNetworkList.GetListItemFileInfo(nlstname, nlstfileid, False)
    
    name = pFileInfo.OutPar('pFileInfo')['KLNLST_FILE_NAME']
    size = pFileInfo.OutPar('pFileInfo')['KLNLST_TOTAL_SIZE']
    
    print('File name: ', name, ' File size: ', size)

    pChunk = NagNetworkList.GetListItemFileChunk(nlstname, nlstfileid, False, 0, size)
    #print(pChunk.respose_text)
    
    f = open(downloadpath + name, 'wb')
    f.write(strToBin(pChunk.OutPar('pChunk')))
    f.close()

    return
     
def Connect(server_url = '', server_port = 13299, sUser = '', sPassword = '', hostaddress=''):
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
        server_main = ConnectBasicAuth(server_url, user, password, internal_user_flag = True, verify = False, vserver = '')
    else:
        server_main = ConnectNTLMAuth(server_url, verify = False, vserver = '')

    if hostaddress is None:
        hostaddress = GetHostNameByHostFQDN(server_main, socket.getfqdn());
        
    # prepare token for gateway auth    
    print ('-- Prepare nagent gateway connection --')
    token = PrepareNagentGatewayConnection(server_main, wsHostName = hostaddress) # prepare token to connect to nagent on current device; or use wanted device fqdn here
    server = ConnectNagentGatewayAuth(server_url, token)

    return server
    
def AddServerAddressArgs(parser):
    group_address = parser.add_argument_group()
    group_address.add_argument('-serveraddress', action='store', help='(optional) address where KSC server is located, for example "https://ksc.example.com". If no -address option is used, suppose KSC server is installed on current machine')
    group_address.add_argument('-port', type=int, action='store', help='(optional) KSC server port, by default port 13299 is used')
    group_address.add_argument('-user', action='store', help='(optional) internal account for basic auth on KSC server and for preparation steps for gateway connection')
    group_address.add_argument('-password', action='store', help='(optional) password to account for basic auth on KSC server and for preparation steps for gateway connection')
    group_address.add_argument('-hostaddress', action='store', help='(optional) address of host where Nlst files are located, for example "myworkstation.avp.ru". If no -hostaddress option is used, suppose to use current machine')
    group_address.add_argument('-nlstname', action='store', help='(optional) network list name ("Quarantine", "Backup", "TIF"). If no -nlstname option is used, suppose to use "Backup"')
    group_address.add_argument('-nlstfileid', action='store', help='Id of network list file to download')
    group_address.add_argument('-downloadpath', action='store', help='Destination file path')
    return

def main():
    """ Depending on command line arguments this module shows KSC connection with different authentication methods.
    Address of KSC server is optional argument, and if not stated then current machine FQDN is used (supposed tests are run on machine where KSC server is installed)    
    Samples of usage:
    
    >> python.exe sample_nlst.py -nlstfileid=-1234 -downloadpath c:/work/dump/ -nlstname TEST_KLAKAUT_NETWORK_LIST
    
    """
 
    #argument parsing
    parser = argparse.ArgumentParser(description='This module provides samples of KSC authorization')
    group_auth_type = parser.add_mutually_exclusive_group(required=False)
    AddServerAddressArgs(parser)
    args = parser.parse_args()

    #KSC connection
    server = Connect(args.serveraddress, args.port, args.user, args.password, args.hostaddress) 
    DownloadNlstFile(server, args.nlstname, args.nlstfileid, args.downloadpath)
    
if __name__ == '__main__':
    main()