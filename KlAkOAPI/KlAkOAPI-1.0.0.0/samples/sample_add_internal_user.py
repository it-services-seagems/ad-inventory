# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to add internal user"""

import socket
import uuid
import datetime
from sys import platform
from KlAkOAPI.Params import KlAkArray, paramBinary, strToBin, dateTimeToStr
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.SecurityPolicy import KlAkSecurityPolicy
from KlAkOAPI.DataProtectionApi import KlAkDataProtectionApi

 
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
    """ This sample shows how you can add internal user """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    # protect user's password
    oDataProtectionApi = KlAkDataProtectionApi(server)
    bPasswordProtected = oDataProtectionApi.ProtectUtf16StringGlobally("test1234!").RetVal()
    
    # add user
    oUsers = KlAkSecurityPolicy(server)
    strUserName = "User_" + dateTimeToStr(datetime.datetime.now()).replace("-", "_").replace(":", "_")
    nUserID = oUsers.AddUser({"KLSPL_USER_NAME": strUserName, "KLSPL_USER_FULL_NAME": strUserName, "KLSPL_USER_PWD_ENCRYPTED": paramBinary(  (bPasswordProtected))}).RetVal()
    print ('Added user', strUserName, ', id =', nUserID)

    
if __name__ == '__main__':
    main()