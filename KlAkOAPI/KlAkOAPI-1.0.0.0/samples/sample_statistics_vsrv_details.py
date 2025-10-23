# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to view statistics of virtual servers"""

import socket
from sys import platform
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.HostGroup import KlAkHostGroup

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
    
def AcquireStatistics(oHostGroup):
    oStatParams = oHostGroup.GetInstanceStatistics(['KLSRV_ST_VIRT_SERVER_COUNT', 'KLSRV_ST_TOTAL_HOSTS_COUNT', 'KLSRV_ST_VIRT_SERVERS_DETAILS']).RetVal()

    nVSrvCount = oStatParams['KLSRV_ST_VIRT_SERVER_COUNT']
    nHstCount  = oStatParams['KLSRV_ST_TOTAL_HOSTS_COUNT']

    print('GetInstanceStatistics returned: KLSRV_ST_VIRT_SERVER_COUNT=', nVSrvCount, ', KLSRV_ST_TOTAL_HOSTS_COUNT=', nHstCount)

    oVSrvDetails = oStatParams['KLSRV_ST_VIRT_SERVERS_DETAILS']

    print('Virtual server details:')

    for O in oVSrvDetails:
        print('KLSRV_ST_VIRT_SERVER_ID=', O['KLSRV_ST_VIRT_SERVER_ID'])
        print('KLSRV_ST_VIRT_SERVER_NAME=', O['KLSRV_ST_VIRT_SERVER_NAME'])
        if 'KLSRV_ST_VSERVER_HOST_COUNT' in O:
            print('KLSRV_ST_VSERVER_HOST_COUNT=', O['KLSRV_ST_VSERVER_HOST_COUNT'])
        if 'KLSRV_ST_VSERVER_CREATION_DATE' in O:
            print('KLSRV_ST_VSERVER_CREATION_DATE=', O['KLSRV_ST_VSERVER_CREATION_DATE'])
        if 'KLSRV_ST_VSERVER_REAL_HOST_COUNT' in O:
            print('KLSRV_ST_VSERVER_REAL_HOST_COUNT=', O['KLSRV_ST_VSERVER_REAL_HOST_COUNT'])
        if 'KLSRV_ST_VSERVER_IOSMDM_DEV_COUNT' in O:
            print('KLSRV_ST_VSERVER_IOSMDM_DEV_COUNT=', O['KLSRV_ST_VSERVER_IOSMDM_DEV_COUNT'])
        if 'KLSRV_ST_VSERVER_KESMOB_DEV_COUNT' in O:
            print('KLSRV_ST_VSERVER_KESMOB_DEV_COUNT=', O['KLSRV_ST_VSERVER_KESMOB_DEV_COUNT'])
        if 'KLSRV_ST_VSERVER_TRIAL_LIC_EXISTS' in O:
            print('KLSRV_ST_VSERVER_TRIAL_LIC_EXISTS=', O['KLSRV_ST_VSERVER_TRIAL_LIC_EXISTS'])
        if 'KLSRV_ST_VSERVER_COM_LIC_EXISTS' in O:
            print('KLSRV_ST_VSERVER_COM_LIC_EXISTS=', O['KLSRV_ST_VSERVER_COM_LIC_EXISTS'])
        if 'KLSRV_ST_VSERVER_LAST_COM_LIC_EXPIR' in O:
            print('KLSRV_ST_VSERVER_LAST_COM_LIC_EXPIR=', O['KLSRV_ST_VSERVER_LAST_COM_LIC_EXPIR'])
        print('--')


def main():
    """ This sample shows how you can view statistics of virtual servers """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oHostGroup = KlAkHostGroup(server)
    AcquireStatistics(oHostGroup)

    
if __name__ == '__main__':
    main()