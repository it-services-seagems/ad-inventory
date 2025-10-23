# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to enumerate child servers"""

import time
import socket
from sys import platform
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.ServerHierarchy import KlAkServerHierarchy
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
    
def main():
    """ This sample shows how you can enumerate child servers """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oHostGroup = KlAkHostGroup(server)

    oServerHierarchy = KlAkServerHierarchy(server)
    oChildServers = oServerHierarchy.GetChildServers(-1).RetVal()
    
    if oChildServers == None or len(oChildServers) == 0:
        print('No slave servers found')
    else:
        for oObj in oChildServers:
            oGroupInfo = oHostGroup.GetGroupInfo(oObj['KLSRVH_SRV_GROUPID']).RetVal()
            print('Server''s "' + oObj['KLSRVH_SRV_DN'] + '", id=' + str(oObj['KLSRVH_SRV_ID']) + ', in group ' + oGroupInfo['grp_full_name'] + ' status is ' + (lambda: 'Inactive' if oObj['KLSRVH_SRV_STATUS'] == 0 else 'Active')())

    
if __name__ == '__main__':
    main()