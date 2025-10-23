# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to enumerate groups"""

import socket
from sys import platform
import KlAkOAPI.AsyncActionStateChecker
import KlAkOAPI.Params
from KlAkOAPI.Params import KlAkArray
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
    
def EnumerateGroups(oGroups, nLevel):
    for oGroup in oGroups:
        nId = oGroup['id']
        strName = oGroup['name']
        
        # form indention for logging
        strIndention = '    ' + '  ' * nLevel + '+-'
        
        # log found group
        print(strIndention, 'Subgroup:', strName, ', id:', nId)
        if 'groups' in oGroup:
            groups = oGroup['groups']
            EnumerateGroups(groups, nLevel + 1)
        
def main():
    """ This sample shows how you can enumerate groups """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oHostGroup = KlAkHostGroup(server)
    
    # get id of root group ('Managed devices' group)
    nRootGroupID = oHostGroup.GroupIdGroups().RetVal()

    # enumerate subgroups of root group
    oSubgroups = oHostGroup.GetSubgroups(nRootGroupID, 0).RetVal()
    if oSubgroups == None or len(oSubgroups) == 0:
        print('Root group is empty')
    else:
        EnumerateGroups(oSubgroups, 0)

    
if __name__ == '__main__':
    main()