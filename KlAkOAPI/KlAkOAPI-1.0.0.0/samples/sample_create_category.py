# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create application category"""

import socket
from sys import platform
from KlAkOAPI.Params import KlAkParams
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.FileCategorizer2 import KlAkFileCategorizer2

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
    """ This sample shows how you can create category """
    print (main.__doc__)

    # connect to KSC server using basic auth by default
    server = GetServer()

    # category params
    oExpression = KlAkParams({'ex_type': 3, 'str': 'e4d909c290d0fb1ca068ffaddf22cbd0', 'str_op': 0})
    pCategory = KlAkParams({'name': 'TestDenyList-1', 'CategoryType': 0, 'inclusions': [ oExpression ]})

    # create category
    oCategoryID = KlAkFileCategorizer2(server).CreateCategory(pCategory).RetVal()
    print('New category id =', oCategoryID)
    
if __name__ == '__main__':
    main()