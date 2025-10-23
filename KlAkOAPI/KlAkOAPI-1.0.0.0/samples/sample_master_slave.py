# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create primary-secondary relations"""

import socket
from KlAkOAPI.Params import KlAkParams
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.ServerHierarchy import KlAkServerHierarchy
from KlAkOAPI.HostGroup import KlAkHostGroup

strMasterServer = 'https://ksc-master.example.com'
strSlaveServer  = 'https://ksc-slave.example.com'
nMasterBasePort = 13000
nMasterOapiPort = 13299
nSlaveBasePort = 13000
nSlaveOapiPort = 13299
strMasterUser = 'klakoapi_test'
strMasterPassword = 'test1234!'
strSlaveUser = 'klakoapi_test'
strSlavePassword = 'test1234!'

SSLVerifyCert = 'C:\\ProgramData\\KasperskyLab\\adminkit\\1093\\cert\\klserver.cer'

def GetServerHostName(server):
    oSlaveInfo = KlAkHostGroup(server).GetStaticInfo(None).RetVal()
    print('oSlaveInfo', oSlaveInfo)
    return oSlaveInfo['KLADMSRV_SERVER_HOSTNAME']


def GetSlaveServer(server):
    """ Acquire information about secondary servers in Managed devices group and returns information about first of them """
    oHostGroup = KlAkHostGroup(server)
    nRootGroupID = oHostGroup.GroupIdGroups().RetVal()
    
    arrChildren = KlAkServerHierarchy(server).GetChildServers(nRootGroupID).RetVal()
    if arrChildren == None or len(arrChildren) == 0:
        print('There are no child servers to connect')
    else:
        return arrChildren[0]
        

def GetCert(server):
    srvInfo = KlAkHostGroup(server).GetStaticInfo(['KLADMSRV_SERVER_CERT']).RetVal()
    return srvInfo['KLADMSRV_SERVER_CERT']


def RemoveSlave(server, lSlaveId):
    print('connect to secondary')
    #connect to the secondary before removing it
    oSlaveServer = KlAkAdmServer.Create(strSlaveServer + ':' + str(nSlaveOapiPort), strSlaveUser, strSlavePassword, verify = False)
    
    oSlaveHostGroup = KlAkHostGroup(oSlaveServer)
    strServerHostName = GetServerHostName(oSlaveServer)

    oSlaveHostGroup.SS_Write(strServerHostName, 'SS_SETTINGS', '1093', '1.0.0.0', 'KLSRV_MASTER_SRV', 7, {'KLSRV_MASTER_SRV_USE': False})
        
    print('Delete slave')
    oServerHierarchy = KlAkServerHierarchy(server)
    oServerHierarchy.DelServer(lSlaveId)
        
        
def AddSlave(server, strDisplayName, lGroupId):
    lId = None
    #connecting to the secondary server candidate
    print('Connect to secondary')
    oSlaveServer = KlAkAdmServer.Create(strSlaveServer + ':' + str(nSlaveOapiPort), strSlaveUser, strSlavePassword, verify = False)
    oServerHierarchy = KlAkServerHierarchy(server)
    lId = oServerHierarchy.RegisterServer(strDisplayName, lGroupId, GetCert(oSlaveServer), '', {}).RetVal() 
    
    #now add "secondary server" to primary server
    print('Add secondary server \"' + strDisplayName + '\" into group ', lGroupId)

    oSlaveHostGroup = KlAkHostGroup(oSlaveServer)
    strServerHostName = GetServerHostName(oSlaveServer)
    
    strMasterServerAddress = strMasterServer + ':' + str(nMasterBasePort)    
    oMasterInfo = KlAkParams({'KLSRV_MASTER_SRV_USE': True, 'KLSRV_MASTER_SRV_SSL_CERT': GetCert(server), 'KLSRV_MASTER_SRV_PASSIVE_SLAVE': False, 'KLSRV_MASTER_SRV_ADDR': strMasterServerAddress})
    
    oSlaveHostGroup.SS_CreateSection(strServerHostName, 'SS_SETTINGS', '1093', '1.0.0.0', 'KLSRV_MASTER_SRV')
    oSlaveHostGroup.SS_Write(strServerHostName, 'SS_SETTINGS', '1093', '1.0.0.0', 'KLSRV_MASTER_SRV', 7, oMasterInfo)    
    
    return lId


def main():
    """ This sample shows how you can create primary-secondary relations """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = KlAkAdmServer.Create(strMasterServer + ':' + str(nMasterOapiPort), strMasterUser, strMasterPassword, verify = SSLVerifyCert)
     
    childServer = GetSlaveServer(server)
    if childServer == None:
        AddSlave(server, 'test_slave', 0)
    else:
        RemoveSlave(server, childServer['KLSRVH_SRV_ID'])

    
if __name__ == '__main__':
    main()
