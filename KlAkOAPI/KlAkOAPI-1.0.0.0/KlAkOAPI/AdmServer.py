# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

""" Module describes KlAkAdmServer class that provides connection to KSC server.
Requests module is used for creating HTTP over TLS connection 
#TODO: pip freeze > requirements.txt
"""

import requests
import base64
import json
import sys
import urllib3
import certifi
import http
import time
import os
import re

from enum import Enum
from .Error import KlAkError
from .Base import KlAkBase
from .Params import KlAkParamsEncoder

class KlAkAdmServer(KlAkBase):
    """ KlAkAdmServer provides authentication and connection to KSC server
    To communicate with any KSC objects you should first connect to KSC server using one of proposed authentication methods
    Since KlAkAdmServer object is created and Connect() method is called successfully this object can be used 
    for initialization any other objects. Every other KlAk... type require KlAkAdmServer object in constructor """
    
    class AuthType (Enum):
        BASIC_AUTH = 0,
        TOKEN_AUTH = 1,
        WEB_TOKEN_AUTH = 2,
        GATEWAY_AUTH = 3,
        NTLM_AUTH = 4
        
    def __init__(self, ksc_server_url, vserver = "", api_ver = "v1.0", auth_type = AuthType.BASIC_AUTH):
        self.ksc_server_url = ksc_server_url
        self.api_ver = "/api/" + api_ver + "/"
        self.vserver = vserver
        self.auth_type = auth_type  
        self.user_account = None
        self.token = None        
        self.connected = False    
        pass
        
    def __SetAuthType(self, auth_type):
        if self.connected:
            self.Disconnect()
        self.auth_type = auth_type
        
    def __SetAccount(self, user_account, password, domain = '', internal_user = False):
        self.user_account = base64.b64encode(user_account.encode('utf-8')).decode("utf-8")
        self.password = base64.b64encode(password.encode('utf-8')).decode("utf-8")
        self.internal = bool(internal_user)
        self.domain = domain
        
    def __SetToken(self, token):
        self.token = token
        
    def Call(self, path):
        return self.ksc_server_url + self.api_ver + path;        

    def URL(self):    
        return self.ksc_server_url
   
    def __LoginNTLM(self, verify = True):
        # login to server using NTLM, that is multi-step procedure
        import sspi
        import sspicon
        import pywintypes
        import win32security
        clientauth = sspi.ClientAuth('NTLM')
        
        # first, prepare request
        sec_buffer = win32security.PySecBufferDescType()
        error, auth = clientauth.authorize(sec_buffer)     
        auth_header = 'NTLM ' + base64.b64encode(auth[0].Buffer).decode('ASCII')

        response = None
        while response is None or response.status_code == 401:
            auth_headers = {'Authorization': auth_header, **KlAkBase.common_headers }
            auth_headers.update({'X-KSC-VServer': base64.b64encode(self.vserver.encode('utf-8')).decode("utf-8")})
            
            data = {}
            
            response = self.session.post(url = self.Call("login"), headers = auth_headers, data = data, verify = verify)

            # after request is sent, server answers with challenge; we need to response
            if response.status_code == 401:
                # Extract challenge message from server
                challenge = response.headers.get('WWW-Authenticate', '').split()
                if len(challenge) < 2:
                    raise KlAkError('Got empty NTLM challenge from server.')
                elif len(challenge) > 2:
                    raise KlAkError('Did not get exactly one NTLM challenge from server.')

                # Add challenge to security buffer
                pkg_info = win32security.QuerySecurityPackageInfo('NTLM')
                tokenbuf = win32security.PySecBufferType(pkg_info['MaxToken'], sspicon.SECBUFFER_TOKEN)
                tokenbuf.Buffer = base64.b64decode(challenge[1])
                sec_buffer = win32security.PySecBufferDescType()
                sec_buffer.append(tokenbuf)

                # Prepare header for next authorization step
                error, auth = clientauth.authorize(sec_buffer)
                auth_header = 'NTLM ' + base64.b64encode(auth[0].Buffer).decode('ASCII')
                
        return response
            

    def __Login(self, verify = True):    
        """ Connects server on url (given in constructor) using auth_type authentication; for NTLM authentication analyze response and executes challenge if needed """       
        auth_header = ''
        if self.auth_type == self.AuthType.NTLM_AUTH:
            return self.__LoginNTLM(verify)  
            
        if self.auth_type == self.AuthType.BASIC_AUTH:
            auth_header = 'KSCBasic user="' + self.user_account + '", pass="' + self.password + '", domain="'+ self.domain+ '", internal="' + str(int(self.internal)) + '"'
        elif self.auth_type == self.AuthType.TOKEN_AUTH:
            auth_header = 'KSCT ' + self.token
        elif self.auth_type == self.AuthType.WEB_TOKEN_AUTH:
            auth_header = 'KSCWT ' + self.token
        else: # GATEWAY_AUTH
            auth_header = 'KSCGW ' + self.token
            
        auth_headers = {'Authorization': auth_header, **KlAkBase.common_headers }
        auth_headers.update({'X-KSC-VServer': base64.b64encode(self.vserver.encode('utf-8')).decode("utf-8")})
        
        data = {}
        
        response = self.session.post(url = self.Call("login"), headers = auth_headers, data = data, verify = verify)
        
        return response
        
    def __Connect(self, verify = True):
        """ Connects server on url (given in constructor) using auth_type authentication """
        
        self.session = requests.Session()
        
        # make sure we are using the same connection during all the session
        adapter = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1)
        self.session.mount('https://', adapter)

        response = self.__Login(verify)
        
        self.connected = (response.status_code == http.HTTPStatus.OK)
        if self.auth_type == self.AuthType.GATEWAY_AUTH:
            return

        return self.ParseResponse(response.status_code, response.text, retval=False)

    def Create(url, user_account = None, password = None, domain = '', internal_user = False, verify = True, vserver = ''):
        """ Creates, initializes and connects KSC server using basic authentication """
        server = KlAkAdmServer(url, vserver)
        
        if user_account is None or user_account == '':
            return KlAkAdmServer.CreateNTLM(url, verify, vserver)
            
        server.__SetAuthType(KlAkAdmServer.AuthType.BASIC_AUTH)
        server.__SetAccount(user_account, password, domain, internal_user)
        server.__Connect(verify)
        return server
        
    def CreateNTLM(url, verify = True, vserver = ''):
        """ Creates, initializes and connects KSC server using NTLM authentication """
        if sys.platform != "win32":
            raise KlAkError('NTLM is supported on Windows platform only')
        server = KlAkAdmServer(url, vserver)
        server.__SetAuthType(KlAkAdmServer.AuthType.NTLM_AUTH)
        server.__Connect(verify)
        return server
           
    def CreateByToken(url, token, verify = True, vserver = ''):
        """ Creates, initializes and connects KSC server using authentication by token """
        server = KlAkAdmServer(url, vserver)
        server.__SetAuthType(KlAkAdmServer.AuthType.TOKEN_AUTH)
        server.__SetToken(token)
        server.__Connect(verify)
        return server

    def CreateByWebToken(url, token, verify = True, vserver = ''):
        """ Creates, initializes and connects KSC server using authentication by web token """
        server = KlAkAdmServer(url, vserver)
        server.__SetAuthType(KlAkAdmServer.AuthType.WEB_TOKEN_AUTH)
        server.__SetToken(token)
        server.__Connect(verify)
        return server
        
    def CreateGateway(url, token, verify = True):
        """ Creates, initializes and connects KSC server using gateway authentication. Token should be created with CgwHelper.GetSlaveServerLocation / CgwHelper.GetNagentLocation calls """
        server = KlAkAdmServer(url)
        server.__SetAuthType(KlAkAdmServer.AuthType.GATEWAY_AUTH)
        server.__SetToken(token)
        server.__Connect(verify)
        return server
     
    def Get(self, url, range, content_type = 'application/octet-stream', stream = True):
        """ Get method is used to download files such as created with KlAkReportManager.ExecuteReportAsync calls """
        return self.session.get(self.ksc_server_url + url, headers = {'Content-Type': content_type, 'Range': range}, stream = stream)
    
    def DownloadFile(self, url, path):
        """ Downloads file chunk by chunk; return status code of last downloaded chunk - 200 and 206 mean successful downloading """
        attempts_count = 5
        attempts_left = attempts_count
        start = 0
        while True:
            r = self.Get(url, 'bytes=' + str(start) + '-')
            if r.status_code == http.HTTPStatus.OK or r.status_code == http.HTTPStatus.PARTIAL_CONTENT:  
                # file downloaded completely (HTTPStatus.OK / 200) or partially (HTTPStatus.PARTIAL_CONTENT / 206)  
                start += len(r.content)
                with open(path, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
                # downloaded completely -> return
                if r.status_code == http.HTTPStatus.OK or len(r.content) == 0 or not 'Content-Range' in r.headers:  
                    return r.status_code
                # analyze 'Content-Range' header
                m = re.match( 'bytes[\s|=](?P<range>[*]|(?P<chunk_start>\d+)[-](?P<chunk_end>\d+))/(?P<full_size>[*]|\d+)', r.headers['Content-Range'])
                if m == None:
                    raise KlAkError('Cannot parse content range ' + r.headers['Content-Range'])
                m_range = m.group('range')
                m_size  = m.group('full_size')
                if m_range == None or m_size == None:
                    raise KlAkError('Cannot parse content range ' + r.headers['Content-Range'])
                m_chunk_start = m.group('chunk_start')
                m_chunk_end = m.group('chunk_end')
                if m_range != "*" and m_size != "*" and m_chunk_end != None:
                    # downloaded all the range in 'Content-Range' -> return
                    if int(m_chunk_end) >= int(m_size) - 1:
                        return r.status_code
                attempts_left = attempts_count
            else:
                if r.status_code == http.HTTPStatus.SERVICE_UNAVAILABLE: 
                    # server is busy / 503, -> try once again, not more than certain amount of attempts
                    if attempts_left == 0:
                        return r.status_code
                    attempts_left -= 1 
                    # wait some time before trying again
                    time.sleep(10)
                else:   
                    # 404 not found, 500 internal server error, etc
                    return r.status_code

    def Put(self, url, start, end, full_size, data):
        """ Put method is used to upload files such as with NagRdu.GetUrlToUploadFileToHost  calls 
            For large files (full_size > 1Mb) Put should be called multiple times chunk by chunk; in each chunk full_size should be presented, such as:
            server.Put(upload_url, start = 0,   end = 99,  full_size = 125, data = data_chunk1)
            server.Put(upload_url, start = 100, end = 124, full_size = 125, data = data_chunk2) """
        if start == None and end == None:
            start = 0
            end = full_size - 1
        content_range = 'bytes ' + str(start) + '-' + str(end) + '/' + str(full_size)
        return self.session.put(self.ksc_server_url + url, headers = {'Content-Type': 'application/zip', 'Content-Range': content_range, 'Expect': '100-continue'}, data = data)
        
    def UploadFile(self, upload_url, upload_filepath):
        """ Uploads file chunk by chunk """
        # calculate full size to download and max size of chunk
        file_size = os.stat(upload_filepath).st_size
        file_chunk_size = 1048576  # 1Mb
        attempts_count = 5
        attempts_left = attempts_count
        start = 0
        with open(upload_filepath, 'rb') as f:
            # read first chunk
            bdata = f.read(file_chunk_size)
            while True:
                # file is read till the end -> return
                if bdata == None or bdata == b'':
                    break
                # upload chunk
                r = self.Put(upload_url, start, f.tell() - 1, file_size, bdata)
                if r.status_code == http.HTTPStatus.CREATED:
                    # chunk uploaded successfully - HTTPStatus.CREATED / 201
                    start = f.tell()
                    bdata = f.read(file_chunk_size)
                    attempts_left = attempts_count
                    continue
                elif r.status_code == http.HTTPStatus.SERVICE_UNAVAILABLE: 
                    # server is busy / 503, -> try once again, not more than certain amount of attempts
                    if attempts_left == 0:
                        return r.status_code
                    attempts_left -= 1 
                else:   
                    # 404 not found, 500 internal server error, etc
                    return r.status_code
             
    def Disconnect(self):
        self.session.close()
        self.connected = False
                
