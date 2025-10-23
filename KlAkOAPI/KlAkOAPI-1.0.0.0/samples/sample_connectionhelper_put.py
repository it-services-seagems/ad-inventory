# !/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to upload and execute file on remote host.
KlAkOAPI package is a wrapper library for interacting Kaspersky Security Center (aka KSC) server with KSC Open API
For detailed description of KSC Open API protocol please refer to KLOAPI documentation pages
"""

import sys
import os
import socket
import zipfile
import time
import tempfile
import argparse
from KlAkOAPI.Base import MillisecondsToSeconds
from KlAkOAPI.Params import KlAkParams, paramParams
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.Error import KlAkError, KlAkResponseError
from KlAkOAPI.AsyncActionStateChecker import KlAkAsyncActionStateChecker
from KlAkOAPI.NagRdu import KlAkNagRdu
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.CgwHelper import KlAkCgwHelper
from KlAkOAPI.GatewayConnection import KlAkGatewayConnection
import KlAkOAPI.ConnectionHelper

strResultFolder      = 'results'  
strFilenameArchive   = 'test.zip'
strFilenameExecutble = 'test.bat'
strFilenameResult    = 'test_result.zip'

def CreateFileForUpload(strArchiveFilename, strExecutableFilename):
    """ Creates archive with folder 'utility' with .bat-file in it for further test of scenario execution. For details see section NagRdu::ExecuteFileAsync in KLOAPI documentation """
    strUtilityFoldername = 'utility'
    
    # create folder for result
    if not os.path.exists(strResultFolder):
        os.makedirs(strResultFolder)
 
    strArchivePath = os.path.join(strResultFolder, strArchiveFilename)
    
    # create archive
    with tempfile.TemporaryDirectory() as strTmpFoldername:
        strUtilityPath = os.path.join(strTmpFoldername, strUtilityFoldername)
        strExecutablePath = os.path.join(strUtilityPath, strExecutableFilename)
        # create folder 'utility'
        os.makedirs(strUtilityPath)
        # create .bat file, write echo statement into it
        with open(strExecutablePath, 'w') as f:
            f.write('echo 123')
        # create archive containing .bat file
        with zipfile.ZipFile(strArchivePath, 'w') as hArchive:
            hArchive.write(strUtilityPath, strUtilityFoldername)
            hArchive.write(strExecutablePath, os.path.relpath(strExecutablePath, strTmpFoldername))
            
    return strArchivePath
            

def ReadArchive(strArchiveFilename):
    """ Reads archive according to structure of archive due to NagRdu::GetUrlToDownloadFileFromHost section in KLOAPI documentation """
    result = ''
    with tempfile.TemporaryDirectory() as strTmpFoldername:
        with zipfile.ZipFile(strArchiveFilename, 'r') as hArchive:
            hArchive.extractall(strTmpFoldername)
        with open(os.path.join(strTmpFoldername, 'result\\stdout.txt'), 'r') as f:
            result = f.read()
            
    return result                

def UploadAndExecuteOnHost(server):
    """ Upload file on host using gateway connection to host's nagent, execute and download results """         
    print ('-- Upload and excution on remote machine sample --')
    oNagRdu = KlAkNagRdu(server)
    
    # create archive for upload
    print('- create archive with test executable inside')
    full_archive_filename = CreateFileForUpload(strFilenameArchive, strFilenameExecutble) 
    
    # get url for uploading on remote machine and upload
    print('- upload')
    upload_url = oNagRdu.GetUrlToUploadFileToHost().RetVal()
    server.UploadFile(upload_url, full_archive_filename)

    # execute on remote machine
    print('- execute async uploaded file')
    strActionGuid = oNagRdu.ExecuteFileAsync(upload_url, strFilenameExecutble, '').RetVal()
    
    # check for result of asynchronous action
    asyncActionStateChecker = KlAkAsyncActionStateChecker (server)
    while True:
        res = asyncActionStateChecker.CheckActionState(strActionGuid)
        if res.OutPar('bFinalized'):
            if res.OutPar('bSuccededFinalized'):
                # got asynchronous result: success 
                print ('  File executed successfully')
                pState = KlAkParams(res.OutPar('pStateData'))
                
                # download archive with results of execution
                print('- download result of asynk execution')
                strDownloadFromUrl = oNagRdu.GetUrlToDownloadFileFromHost(pState['LastActionResult']).RetVal() 
                strDownloadToFilepath = os.path.join(strResultFolder, strFilenameResult)
                server.DownloadFile(strDownloadFromUrl, strDownloadToFilepath)
                print('  Result output is successfully downloaded to ', strDownloadToFilepath)
                
                result = ReadArchive(strDownloadToFilepath)
                print('Here is the result of execution uploaded file:\n' + result)
            else:
                # got asynchronous result: some error occurred
                oErrDescription = KlAkParams(res.OutPar('pStateData'))
                print('Cannot execute file:', oErrDescription)
            break
        else:
            # asynchronous result is not ready yet - need to wait for lNextCheckDelay milliseconds
            time.sleep(MillisecondsToSeconds(res.OutPar('lNextCheckDelay')))

    
def main():
    """ This sample shows how you can upload file on host, execute and check result """
    print (main.__doc__)
        
    #argument parsing
    parser = argparse.ArgumentParser()
    
    KlAkOAPI.ConnectionHelper.AddConnectionArgs(parser)
    
    args = parser.parse_args()
    
    #connect to KSC server using basic auth by default
    server = KlAkOAPI.ConnectionHelper.ConnectFromCmdline(args)

    # connect to nagent on current machine
    #server = GetNagent()
    
    UploadAndExecuteOnHost(server)

    
if __name__ == '__main__':
    main()