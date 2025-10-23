# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAk package to view and modify notification properties"""

import socket
from sys import platform
from KlAkOAPI.Params import KlAkParams
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.EventNotificationProperties import KlAkEventNotificationProperties

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
    
def Start(server):
    oNotifProps = KlAkEventNotificationProperties(server)

    print('Dumping default settings...')
    oSettings = oNotifProps.GetDefaultSettings().RetVal()
    print(oSettings)

    print('Done.')

    strEmail = 'testuser@fromscript.com'
    print('Setting "KLEVP_ND_EMAIL_FROM" parameter value to '' + strEmail + ''')

    oSettings.AddString('KLEVP_ND_EMAIL_FROM', strEmail)
    oNotifProps.SetDefaultSettings(oSettings)

    print('Dumping updated settings...')

    oSettings = oNotifProps.GetDefaultSettings().RetVal()
    print(oSettings)

    print('Done.')

def main():
    """ This sample shows how you can view and modify notification properties """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    Start(server)

    
if __name__ == '__main__':
    main()