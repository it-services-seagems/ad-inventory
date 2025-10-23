# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to send mail"""

import socket
import uuid
from sys import platform
import KlAkOAPI.Params
from KlAkOAPI.AdmServer import KlAkAdmServer
import KlAkOAPI.IWebUsersSrv 

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
    """ This sample shows how you can send mail. Notification settings should be set up in advance, including SMTP, ESMTP, etc """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()
 
    print('Sending email...')

    oOptions = KlAkOAPI.Params.KlAkParams({'MailRecipients': ['example@example.com'], 'MailSubject': 'Test qr-code email message', 'MailBodyType': 'html'})

    oQrCode = KlAkOAPI.Params.KlAkParams({})
    #base64 encoded png picture
    oQrCode.AddBinary('QrCodePicture', b'iVBORw0KGgoAAAANSUhEUgAAAMgAAADIAQMAAACXljzdAAAABlBMVEX///8AAABVwtN+AAABLElEQVRYw+2XvRHDIAyFxaWg9AiM4s0csplHYQSXFBzKk0ic/zZSYZ0p4Gt0D54kEx1xxH+DJVaswIWibLob0rCmlWjuEaRgt/ghE7dpPW2zZl3OXLwRmjjU1L0S/pm1HdHb3hX9eAeWZLgEiUPO5Yt/LMmNb8T1e40xJLzN6hL6cLA9aZoyYGC+1ARFsyMywyKSNckxdF08ERyLV6K8wfDcMawJ7AuXnBiKikvy47Y9E1QcfCTeHkKn7IZIQWR5B9A6S71+1tqYIOV205WHvRc/hLXPYXZR//S4e9ue7J2YKHV6uW1zMvocbpvFJeVc33qwJXnMB3Vk7YnoXNV05tN6nbozMuYDFL/gj8AlOLvIuMyOyL20QMsc2RXZ/xulXUQo+uYfS3LEEfZxBUOv1KUQvtGnAAAAAElFTkSuQmCC')
    oQrCode.AddString('QrCodePictureName', 'testpic.png')

    oOptions.AddString('MailBody', '<h2>Unordered List with Default Bullets</h2><ul><li>Entry 1</li><li>Entry 2</li><li>Entry 3</li></ul>')
    oOptions.AddArray('QrCodes', [oQrCode])
    
    print(oOptions)
    
    KlAkOAPI.IWebUsersSrv.KlAkIWebUsersSrv(server).SendEmail(oOptions, str(uuid.uuid4()))

    print('...OK sending email')


    
if __name__ == '__main__':
    main()