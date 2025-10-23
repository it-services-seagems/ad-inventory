# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create groups structure same as AD OU"""

import socket
import win32com.client
from sys import platform
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
    
def GetDefaultNamingContext():
    # returns default AD naming context   
    oRootDSE = win32com.client.GetObject('LDAP://RootDSE')
    strDefaultNamingContext = oRootDSE.Get('defaultNamingContext')
    print("DefaultNamingContext is " + strDefaultNamingContext)
    return strDefaultNamingContext

def ProcessOU(hostGroup, nGroupID, command, strDN, nLevel):
    """" Recursively process AD organizational units and create correspondent group structure in KSC. Used in sample 3c """
    # set query string for command object
    command.CommandText = '<LDAP://' + strDN + '>;(&(objectCategory=organizationalUnit)(|(!(showInAdvancedViewOnly=*))(showInAdvancedViewOnly=0)));name, distinguishedName;oneLevel'
    rs = command.Execute()[0]

    # process returned recordset
    while not rs.EOF:
        strNewName = rs.Fields('name').Value
        strNewDN = rs.Fields('distinguishedName').Value

        # log found OU with proper indentation
        print('  ' * nLevel, '+-', strNewName)

        # create KSC group for found OU
        nIdNewGroup = hostGroup.AddGroup({'name': str(strNewName), 'parentId': nGroupID}).RetVal()

        # process subOUs recursively
        ProcessOU(hostGroup, nIdNewGroup, command, strNewDN, nLevel+1)
        
        rs.MoveNext()
    
def main():
    """ This sample shows how you can create groups structure same as AD OU """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    strDefaultNamingContext = GetDefaultNamingContext()
    
    # prepare connection to AD
    oConnection = win32com.client.Dispatch('ADODB.Connection')
    oConnection.Provider = 'ADSDSOObject'
    oConnection.Open('Active Directory Provider')
    
    # prepare command object
    oCommand = win32com.client.Dispatch('ADODB.Command')
    oCommand.ActiveConnection = oConnection
        
    oHostGroup = KlAkHostGroup(server)
    strGroupName = 'TestGroup'

    # create new group
    nRootGroupID = oHostGroup.GroupIdGroups().RetVal()
    nGroupId = oHostGroup.AddGroup({'name': strGroupName, 'parentId': nRootGroupID}).RetVal()
    
    # process organisation units
    print('Processing organization units')    
    ProcessOU(oHostGroup, nGroupId, oCommand, strDefaultNamingContext, nLevel=1)
    
    # close conection
    oConnection.Close()
    
    
if __name__ == '__main__':
    main()