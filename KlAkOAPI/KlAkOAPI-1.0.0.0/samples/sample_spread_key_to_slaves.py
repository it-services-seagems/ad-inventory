# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to enumerate child servers"""

import time
import socket
import argparse
from sys import platform
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.ServerHierarchy import KlAkServerHierarchy
from KlAkOAPI.LicenseKeys import KlAkLicenseKeys
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams, strToBin
from KlAkOAPI.CgwHelper import KlAkCgwHelper
from KlAkOAPI.GatewayConnection import KlAkGatewayConnection    

def ConnectMainServer(server_url, cert):
    """Connects to main KSC server"""

    username = None # for Windows use NTLM by default
    password = None
    server = KlAkAdmServer.Create(server_url, username, password, verify = cert)
    
    return server

def ConnectToSlave(server_main, server_main_url, slave_id):
    cgwHelper = KlAkCgwHelper(server_main)
    slaveLocation = cgwHelper.GetSlaveServerLocation(slave_id).RetVal()    
    
    arrLocation = []
    arrLocation.append(paramParams(slaveLocation))
    
    gatewayConnection = KlAkGatewayConnection(server_main)
    response = gatewayConnection.PrepareGatewayConnection(arrLocation)
    token_on_slave = response.OutPar('wstrAuthKey')
    
    slaveServer = KlAkAdmServer.CreateGateway(server_main_url, token_on_slave, False)
    
    if slaveServer.connected:
        print ('Slave connected successfully!')
        return slaveServer  

    print ('Slave connection failed')
        
    return None  

def InstallKey(slaveServer, keyInfo):
    licenseKeys = KlAkLicenseKeys(slaveServer)
    
    lic_serial = licenseKeys.InstallKey(KlAkParams(keyInfo)).RetVal()
    licenseKeys.SaasTryToInstall(KlAkParams({"KLLIC_SERIAL": lic_serial}), True)

def LoadKeyBody(server_main, lic_serial):   
    licenseKeys = KlAkLicenseKeys(server_main)
    
    return licenseKeys.GetKeyData(KlAkParams({"KLLIC_SERIAL": lic_serial, "KLLICSRV_KEYDATA": True})).RetVal()
    
    
def AddArgs(parser):
    group_address = parser.add_argument_group()
    group_address.add_argument('-address', action='store', help='(optional) address and port of main server, for example "server.avp.ru:13299". If no -address option is used, suppose to use current machine')
    group_address.add_argument('-cert', action='store', help='Path to certificate file of main server')
    group_address.add_argument('-serial', action='store', help='License serial number')
    return
    
def main():
    """ This sample shows how you can install specified license from main server's licenses storage to all child servers """
    
    parser = argparse.ArgumentParser(description='This sample shows how you can set license to all child servers')
    group_auth_type = parser.add_mutually_exclusive_group(required=False)
    
    AddArgs(parser)
    args = parser.parse_args()

    server_address = args.address
    if server_address == None:
        server_address = socket.getfqdn() + ':13299'
    
    server_url = 'https://' + server_address
    server = ConnectMainServer(server_url, args.cert)

    keyInfo = LoadKeyBody(server, args.serial)

    oServerHierarchy = KlAkServerHierarchy(server)
    oChildServers = oServerHierarchy.GetChildServers(-1).RetVal()
    
    if oChildServers == None or len(oChildServers) == 0:
        print('No slave servers found')
    else:
        for oObj in oChildServers:
            print('Server''s "' + oObj['KLSRVH_SRV_DN'] + '", id=' + str(oObj['KLSRVH_SRV_ID']))
            InstallKey(ConnectToSlave(server, server_url, oObj['KLSRVH_SRV_ID']), keyInfo)

  
if __name__ == '__main__':
    main()