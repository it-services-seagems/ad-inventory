# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to generate reports"""

import sys
import socket
import time
import datetime
import os
import argparse
import base64
import uuid
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramArray, paramParams, paramDateTime, dateToStr, dateTimeToStr
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.Base import MillisecondsToSeconds
from KlAkOAPI.Error import KlAkError, KlAkResponseError
from KlAkOAPI.ReportManager import KlAkReportManager
from KlAkOAPI.AsyncActionStateChecker import KlAkAsyncActionStateChecker
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.SrvView import KlAkSrvView

                        
strResultFolder = 'results'            
    
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

def AddUserEffRightsReport(oReportManager, userId):
    """ Add User Effective Rights Report """
    oInfo = oReportManager.GetDefaultReportInfo(40).RetVal()   # RT_USERS_EFF_RIGHTS
    oInfo["RPT_DN"] = "Sample RT_USERS_EFF_RIGHTS"   

    extra = KlAkParams({})
    extra.AddLong('KLRPT_TRUSTEE_ID', userId)

    oInfo.AddParams('RPT_EXTRA_DATA', extra)
        
    return oReportManager.AddReport(oInfo).RetVal()

      
def GenerateReport(server, oReportManager, nReportId):
    """ Generates a report """
    print('Creating a report')

    # compose options
    options_format = KlAkParams({})
    options_format.AddInt('KLRPT_MAX_RECORDS_DETAILS', 3000)
    options_format.AddInt('KLRPT_TARGET_TYPE', 0)
    options_format.AddInt('KLRPT_XML_TARGET_TYPE',  0)  # report format here: 0 for html, 1 for xls, 2 for pdf
    options_format.AddBool('KLRPT_PDF_LANDSCAPE',  True)
    options_format.AddInt('KLRPT_PDF_PAGE_SIZE',  9)
    
    options_products = KlAkParams({})
    options_products.AddString('KLRPT_PROD_NAME', "1093")
    options_products.AddString('KLRPT_PROD_NAME_LOC', "Administration server")
    options_products.AddString('KLRPT_PROD_VER', "1.0.0.0")
    options_products.AddString('KLRPT_PROD_VER_LOC', "1.0.0.0")

    options_timezone = KlAkParams({})
    options_timezone.AddInt('RPT_TZ_BIAS', -180)
    options_timezone.AddInt('RPT_TZ_DAYLIGHT_BIAS', -60)
    options_timezone.AddParams('RPT_TZ_DAYLIGHT_DATE', {'RPT_STM_DAY':0, 'RPT_STM_DAYOFWEEK':0, 'RPT_STM_HOUR':0, 'RPT_STM_MILLISECOND':0, 'RPT_STM_MINUTE':0, 'RPT_STM_MONTH':0, 'RPT_STM_SECOND':0, 'RPT_STM_YEAR':0})
    options_timezone.AddString('RPT_TZ_DAYLIGHT_NAME', "Russia TZ 2 Daylight Time")
    options_timezone.AddInt('RPT_TZ_STD_BIAS', 0)
    options_timezone.AddString('RPT_TZ_STD_NAME', "Russia TZ 2 Standard Time")
    options_timezone.AddParams('RPT_TZ_STD_DATE', {'RPT_STM_DAY':0, 'RPT_STM_DAYOFWEEK':0, 'RPT_STM_HOUR':0, 'RPT_STM_MILLISECOND':0, 'RPT_STM_MINUTE':0, 'RPT_STM_MONTH':0, 'RPT_STM_SECOND':0, 'RPT_STM_YEAR':0})
    
    options = KlAkParams({})
    options.AddParams('KLRPT_OUTPUT_FORMAT', options_format )
    options.AddArray('KLRPT_LOC_PRODUCTS', [ paramParams(options_products) ])
    options.AddInt('RPT_LOC_LOCALE', 2057)
    options.AddParams('RPT_TIMEZONE_INFO', options_timezone)
         
    # generate report with proper id and proper options
    strRequestId = oReportManager.ExecuteReportAsync(nReportId, options).OutPar('strRequestId')
    
    # check for result of asynchronous action
    asyncActionStateChecker = KlAkAsyncActionStateChecker (server)
    while True:
        res = asyncActionStateChecker.CheckActionState(strRequestId)
        bFinalized, bSuccededFinalized, lStateCode, pStateData, lNextCheckDelay = res.OutPar('bFinalized'), res.OutPar('bSuccededFinalized'), res.OutPar('lStateCode'), res.OutPar('pStateData'), res.OutPar('lNextCheckDelay')
        if bFinalized:
            if bSuccededFinalized:
                # got asynchronous result: success
                if not 'KLRPT_OUTPUT_FILE' in pStateData:
                    raise KlAkResponseError('Report was marked as generated successfully, but expected field KLRPT_OUTPUT_FILE is absent in response, nothing to download')                
                
                # create folder for result
                if not os.path.exists(strResultFolder):
                    os.makedirs(strResultFolder)
        
                # download result file
                print ('Report generated successfully, ready to download')
                file_name, file_ext = os.path.splitext(pStateData['KLRPT_OUTPUT_FILE'])
                download_filename = os.path.join(strResultFolder, 'report' + file_ext)
                server.DownloadFile(pStateData['KLRPT_OUTPUT_FILE'], download_filename)
                
                # download charts if needed (report in html format needs all the images as separate files)
                if 'KLRPT_OUTPUT_CHART' in pStateData:
                    chartpath = os.path.join(strResultFolder, os.path.basename(pStateData['KLRPT_OUTPUT_CHART']))
                    print('downloading', pStateData['KLRPT_OUTPUT_CHART'], 'to file', chartpath)
                    server.DownloadFile(pStateData['KLRPT_OUTPUT_CHART'], chartpath)
                    print('Chart download successfully')
                
                # download logo if needed (report in html format needs all the images as separate files)
                if False: #'KLRPT_OUTPUT_LOGO' in pStateData:
                    logopath = os.path.join(strResultFolder, os.path.basename(pStateData['KLRPT_OUTPUT_LOGO']))
                    print('downloading', pStateData['KLRPT_OUTPUT_LOGO'], 'to file', logopath)
                    server.DownloadFile(pStateData['KLRPT_OUTPUT_LOGO'], logopath)
                    print('Logo download successfully')
                
                print ('Report downloaded to:', download_filename)
            else:
                # got asynchronous result: some error occurred
                err_description = KlAkParams(res.OutPar('pStateData'))
                print('Cannot create report:', err_description['GNRL_EA_DESCRIPTION'], '(error code ' + str(err_description['KLBLAG_ERROR_INFO']['KLBLAG_ERROR_CODE']) + ')')
            return download_filename
        else:
            # asynchronous result is not ready yet - need to wait for lNextCheckDelay milliseconds
            time.sleep(MillisecondsToSeconds(lNextCheckDelay))

def FindUser(server, strUsername):
    oSrvView = KlAkSrvView(server)
    wstrIteratorId = oSrvView.ResetIterator('GlobalUsersListSrvViewName', '(&(ul_wstrDisplayName=\"' + strUsername + '\")(ul_nVServer = 0))', ['ul_binId', 'ul_llTrusteeId', 'ul_wstrDisplayName'], [], {}, lifetimeSec = 60*5).OutPar('wstrIteratorId')
    llTrusteeId = -1
    if oSrvView.GetRecordCount(wstrIteratorId).RetVal()  > 0:
        pRecords = oSrvView.GetRecordRange(wstrIteratorId, 0, 1).OutPar('pRecords')
        pRecordsArray = pRecords['KLCSP_ITERATOR_ARRAY']
        if pRecordsArray != None and len(pRecordsArray) > 0:
            llTrusteeId = pRecordsArray[0]['ul_llTrusteeId']        
    oSrvView.ReleaseIterator(wstrIteratorId)
    
    if llTrusteeId == -1:
        print('User', strUsername, 'not found')
        return
        
    return llTrusteeId

def AddArgs(parser):
    group_address = parser.add_argument_group()
    group_address.add_argument('-user', action='store', help='(optional) User name to generate report for. If no -user option is used, suppose "UnitTestUser"')
    
def main():
    """ This sample shows how you can create report of effective user rights for specified user """
    print (main.__doc__)
    
    #argument parsing
    parser = argparse.ArgumentParser(description='This module provides sample of how you can create report of effective user rights for specified user')
    AddArgs(parser)
    args = parser.parse_args()
    
    # connect to KSC server using basic auth by default
    server = GetServer()
    
    # use server object to construct objects wrapping KLOAPI calls 
    oReportManager = KlAkReportManager(server)

    userName = args.user
    print('User name: ', userName)
    
    if userName == '': 
        userName = 'UnitTestUser'
        
    # Get user id by name
    userId = FindUser(server, userName)
    print('User id:', userId)

    if userId != -1:
        # report to be generated
        nReportID = AddUserEffRightsReport(oReportManager, userId)
    
        # create report
        download_filename = GenerateReport(server, oReportManager, nReportID)
        print('Now you can analyse report file: ', download_filename)
    
    
if __name__ == '__main__':
    main()