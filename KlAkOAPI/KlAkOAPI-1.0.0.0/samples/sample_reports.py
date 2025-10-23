# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to generate reports"""

import sys
import socket
import time
import datetime
import os
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
                if 'KLRPT_OUTPUT_LOGO' in pStateData:
                    logopath = os.path.join(strResultFolder, os.path.basename(pStateData['KLRPT_OUTPUT_LOGO']))
                    print('downloading', pStateData['KLRPT_OUTPUT_LOGO'], 'to file', logopath)
                    server.DownloadFile(pStateData['KLRPT_OUTPUT_LOGO'], logopath)
                    print('Logo download successfully')
                
                print ('Report downloaded to:', download_filename)
            else:
                # got asynchronous result: some error occurred
                err_description = KlAkParams(res.OutPar('pStateData'))
                print('Cannot create report:', err_description['GNRL_EA_DESCRIPTION'], '(error code ' + str(err_description['KLBLAG_ERROR_INFO']['KLBLAG_ERROR_CODE']) + ')')
            return
        else:
            # asynchronous result is not ready yet - need to wait for lNextCheckDelay milliseconds
            time.sleep(MillisecondsToSeconds(lNextCheckDelay))

def main():
    """ This sample shows how you can create a report and statistics chart """
    print (main.__doc__)
    
    # connect to KSC server using basic auth by default
    server = GetServer()
    
    # use server object to construct objects wrapping KLOAPI calls 
    oReportManager = KlAkReportManager(server)

    # report to be generated
    nReportID = 1
    
    # list reports
    print('List of reports available on server:')
    arrReportsList = oReportManager.EnumReports().RetVal()
    if arrReportsList != None and len(arrReportsList) > 0:
        for parReport in arrReportsList:
            print ('* ID ' + str(parReport['RPT_ID']) + ': ' + parReport['RPT_DN'])
            if nReportID == parReport['RPT_ID']:
                print('  (the report to be printed)')
    
    # create report
    GenerateReport(server, oReportManager, nReportID)
    
    
if __name__ == '__main__':
    main()