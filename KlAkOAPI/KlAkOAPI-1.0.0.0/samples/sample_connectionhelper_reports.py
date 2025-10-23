# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create reports and statistics charts.
KlAkOAPI package is a wrapper library for interacting Kaspersky Security Center (aka KSC) server with KSC Open API
For detailed description of KSC Open API protocol please refer to KLOAPI documentation pages
"""

import sys
import argparse
import time
from datetime import date, datetime, timezone, timedelta
import os
import base64
from requests import Request
import uuid
import KlAkOAPI.ConnectionHelper
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramArray, paramParams, paramDateTime, dateToStr, dateTimeToStr
from KlAkOAPI.Base import MillisecondsToSeconds
from KlAkOAPI.Error import KlAkError, KlAkResponseError
from KlAkOAPI.ReportManager import KlAkReportManager
from KlAkOAPI.AsyncActionStateChecker import KlAkAsyncActionStateChecker
from KlAkOAPI.ConEvents import KlAkConEvents
from KlAkOAPI.HostGroup import KlAkHostGroup

strResultFolder = 'results'    

def RGB(r, g, b):
    """ Transforms RGB values to int, sample of use: RGB(0xFF, 0x88, 0x88). Used in Sample_GetStatChart """
    return r + (g << 8) + (b << 16)       
                                
def Sample_GenerateReport(server, oReportManager, nReportId):
    """ Generates a report """
    print('Creating a report')
    
    # get info about report
    arrReportsList = KlAkArray(oReportManager.EnumReports().RetVal())
    for report in arrReportsList:
        if nReportId == report['RPT_ID']:
            parReport = report
            break
    
    if parReport == None:
        print('Report with id=' + str(nReportId) + ' was not found. You can find id in "RPT_ID" field of list returned by ReportManager.EnumReports(...) call that is output by this module with -lr argument: "Sample4_Reports.py -lr"')
        return        
    else:    
        print('Creating "', parReport['RPT_DN'], '" with the following details:', parReport)  

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
                download_filename = os.path.join(strResultFolder, 'test' + file_ext)
                server.DownloadFile(pStateData['KLRPT_OUTPUT_FILE'], download_filename)
                
                # download charts if needed (report in html format needs all the images as separate files)
                if 'KLRPT_OUTPUT_CHART' in pStateData:
                    chartpath = os.path.join(strResultFolder, os.path.basename(pStateData['KLRPT_OUTPUT_CHART']))
                    print('downloading', pStateData['KLRPT_OUTPUT_CHART'], 'to file', chartpath)
                    server.DownloadFile(pStateData['KLRPT_OUTPUT_CHART'], '.\\' + chartpath)
                    print('Chart download successfully')
                
                # download logo if needed (report in html format needs all the images as separate files)
                if 'KLRPT_OUTPUT_LOGO' in pStateData:
                    logopath = os.path.join(strResultFolder, os.path.basename(pStateData['KLRPT_OUTPUT_LOGO']))
                    print('downloading', pStateData['KLRPT_OUTPUT_LOGO'], 'to file', logopath)
                    server.DownloadFile(pStateData['KLRPT_OUTPUT_LOGO'], '.\\' + logopath)
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

   
ChartList = ['(Diagram) Current state of the most anti-virus protection (number of hosts with status Critical, Warning and OK). ',  # type 20
'(Diagram) State of the anti-viral protection deployment (number of hosts with nagent and anti-virus, nagent only, nothing). ', # type 31, 
'(Histogram) Amounts of vulnerability instances with different max. vulnerability severity (critical, high, warning, none) during some time intervals. ', # type 50
]   
   
def Sample_GetStatChart(server, oReportManager, nChartType):
    """ Requests for statistics and download the result chart file """
    print('Creating following statistics charts for root group: \n* Current state of the most anti-virus protection (type 20), \n* State of the anti-viral protection deployment (type 31) and \n* Amounts of vulnerability instances with different max. vulnerability severity during last week (type 50, where time interval is set to last week)')
    
    # get root group id
    hostGroup = KlAkHostGroup(server)
    nGroupId = hostGroup.GroupIdGroups().RetVal()
    
    # compose params with dashboards info we want to generate
    parDashboards = KlAkParams({})

    # dash type 31: State of the anti-viral protection deployment (number of hosts with nagent and anti-virus, nagent only, nothing). 
    deploymentUUID = str(uuid.uuid4())
    parDashboards.AddParams(deploymentUUID, {'KLRPT_DSH_TYPE': 31, 'id': nGroupId})
    
    # dash type 20: Current state of the most anti-virus protection (number of hosts with status Critical, Warning and OK). 
    hostsUUID = str(uuid.uuid4())
    parDashboards.AddParams(hostsUUID, {'KLRPT_DSH_TYPE': 20, 'id': nGroupId})
    
    # dash type 50: Amounts of vulnerability instances with different max. vulnerability severity (critical, high, warning, none) during some time intervals.
    vulnerabilitiesUUID = str(uuid.uuid4())
    parDashboards.AddParams(vulnerabilitiesUUID, {'KLRPT_DSH_TYPE': 50, 'KLPPT_StatFinishTime': paramDateTime(datetime.now()), 'KLPPT_StatPeriodInSec': 60 * 60 * 24 * 7})  # time period: 7 days ago from now
	
    # compose one request for three dashboards
    parRequestParams = KlAkParams({})
    parRequestParams.AddParams('KLPPT_DASHBOARD', parDashboards)
    
    # gathering statistics needs time, one dash can be done earlier than others, so check progress by timer
    deploymentChartReady, hostsChartReady, vulnerabilitiesChartReady = False, False, False    
    while not deploymentChartReady or not hostsChartReady or not vulnerabilitiesChartReady:
        
        # request statistics for dashboards that are not ready yet by this time
        print('RequestStatisticsData for', parDashboards)        
        strChartRequestId = oReportManager.RequestStatisticsData(parRequestParams).OutPar('strRequestId')
        
        # wait a bit while statistics is collected and prepared
        time.sleep(15)
        
        # get result
        pResultData = KlAkParams(oReportManager.GetStatisticsData(strChartRequestId).OutPar('pResultData'))        
        if not 'KLPPT_DASHBOARD' in pResultData:
            print ('Result is not ready yet, wait some more time')
            continue
            
        # statistics is ready, now make charts with recieved data
        pDash = pResultData['KLPPT_DASHBOARD']
        
        color_red = RGB(0xFF, 0x88, 0x88) # 8947967
        color_green = RGB(0x61, 0xD4, 0x91) # 9557089
        color_turquoise = RGB(0x92, 0xD4, 0xCF) # 13620370

        # make deployment chart
        if not deploymentUUID in pDash:
            if not deploymentChartReady:
                print ('Deployment chart is not ready yet')
        else:
            # compose params with statistics data for deployment chart
            deploymentDash = pDash[deploymentUUID] 
            chartdata0_deployment = KlAkParams({'data': [deploymentDash.GetValue('nOkCount'), deploymentDash.GetValue('nWrnCount'), deploymentDash.GetValue('nCrtCount')], 'name': deploymentUUID})
            chartdata_deployment = KlAkParams({})
            chartdata_deployment.AddArray('KLRPT_CHART_DATA', [paramParams(chartdata0_deployment)])
            chartdata_deployment.AddString('KLRPT_CHART_DATA_DESC', 'State of the anti-viral protection deployment')
            chartdata_deployment.AddString('KLRPT_CHART_LGND_DESC', 'number of hosts:')
            chartdata_deployment.AddArray('KLRPT_CHART_SERIES', ['both nagent and RTP-product installed', 'just nagent installed', 'whithout nagent installed'])
            chartdata_deployment.AddArray('KLRPT_CHART_SERIES_COLORS', [color_green, color_turquoise, color_red])
            chartdata_deployment.AddBool('KLRPT_CHART_PIE', True)
                
            # create chart and download a result file
            res = oReportManager.CreateChartPNG(chartdata_deployment, {'RPT_CHART_WIDTH': 600, 'RPT_CHART_HEIGHT': 600})
            chart_deployment_filename = os.path.join(strResultFolder, 'deployment_dash.png')
            with open(chart_deployment_filename, 'wb') as f:
                packet = base64.b64decode(res.OutPar('pPngData'))
                f.write(packet)
            print('Deployment chart is ready:', chart_deployment_filename)
                
            # recompose data for furher request if some other statistics are not ready yet - no need re-request deployment statistics
            deploymentChartReady = True
            del parDashboards[deploymentUUID]  
            parRequestParams.AddParams('KLPPT_DASHBOARD', parDashboards)
        
        # make anti-virus protection on hosts chart
        if not hostsUUID in pDash:
            if not hostsChartReady:
                print ('Anti-virus protection on hosts chart is not ready yet')
        else:
            # compose params with statistics data for chart
            hostsDash = pDash[hostsUUID]    
            chartdata0_hosts = KlAkParams({'data': [hostsDash.GetValue('nOkCount'), hostsDash.GetValue('nWrnCount'), hostsDash.GetValue('nCrtCount')], 'name': hostsUUID})
            chartdata_hosts = KlAkParams({})
            chartdata_hosts.AddArray('KLRPT_CHART_DATA', [paramParams(chartdata0_hosts)])
            chartdata_hosts.AddString('KLRPT_CHART_DATA_DESC', 'Current state of the most anti-virus protection ')
            chartdata_hosts.AddString('KLRPT_CHART_LGND_DESC', 'number of hosts with:')
            chartdata_hosts.AddArray('KLRPT_CHART_SERIES', ['Ok protection status', 'Warning protection status', 'Critical protection status'])
            chartdata_hosts.AddArray('KLRPT_CHART_SERIES_COLORS', [color_green, color_turquoise, color_red])
            chartdata_hosts.AddBool('KLRPT_CHART_PIE', True)
                         
            # create chart and download a result file
            res = oReportManager.CreateChartPNG(chartdata_hosts, {'RPT_CHART_WIDTH': 600, 'RPT_CHART_HEIGHT': 600})
            chart_hosts_filename = os.path.join(strResultFolder, 'hosts_dash.png')
            with open(chart_hosts_filename, 'wb') as f:
                packet = base64.b64decode(res.OutPar('pPngData'))
                f.write(packet)
            print('Anti-virus protection on hosts chart is ready:', chart_hosts_filename)

            # recompose data for furher request if some other statistics are not ready yet - no need re-request hosts anti-virus protection statistics
            hostsChartReady = True
            del parDashboards[hostsUUID]
            parRequestParams.AddParams('KLPPT_DASHBOARD', parDashboards)
            
        # make vulnerabilities chart
        if not vulnerabilitiesUUID in pDash:
            if not vulnerabilitiesChartReady:
                print ('Vulnerabilities chart is not ready yet')
        else:
            # compose params with vulnerabilities statistics data for chart
            vulnerabilitiesDash = pDash[vulnerabilitiesUUID]
            
            # rearrange statistics data into day-by-day array for histogram visualization 
            arr_data = KlAkArray([])
            for vulnerability in vulnerabilitiesDash['DSHT_DATA']:
                data_item = KlAkParams({'data': [vulnerability.GetValue('nCrtCount'), vulnerability.GetValue('nHiCount'), vulnerability.GetValue('nWrnCount')]})
                data_item.AddString('name', dateTimeToStr(vulnerability['tmFinish']))
                arr_data.AddParams(data_item)
            
            # compose data list and other options
            chartdata_vulnerabilities = KlAkParams({})
            chartdata_vulnerabilities.AddArray('KLRPT_CHART_DATA', arr_data)
            chartdata_vulnerabilities.AddString('KLRPT_CHART_DATA_DESC', 'Amounts of vulnerability instances with different max. vulnerability severity ')
            chartdata_vulnerabilities.AddString('KLRPT_CHART_LGND_DESC', 'number of :')
            chartdata_vulnerabilities.AddArray('KLRPT_CHART_SERIES', ['critical vulnerabilities', 'high-level vulnerabilities', 'warning-level vulnerabilities'])
            chartdata_vulnerabilities.AddArray('KLRPT_CHART_SERIES_COLORS', [color_red, color_green, color_turquoise])
            chartdata_vulnerabilities.AddBool('KLRPT_CHART_STACK_SERIES', True)
            
            # create chart and download a result file            
            res = oReportManager.CreateChartPNG(chartdata_vulnerabilities, {'RPT_CHART_WIDTH': 1600, 'RPT_CHART_HEIGHT': 1200})
            chart_vulnerabilities_filename = os.path.join(strResultFolder, 'vulnerabilities_dash.png')
            with open(chart_vulnerabilities_filename, 'wb') as f:
                packet = base64.b64decode(res.OutPar('pPngData'))
                f.write(packet)
            print('Vulnerabilities chart is ready:', chart_vulnerabilities_filename)
             
            # recompose data for furher request if some other statistics are not ready yet - no need re-request vulnerabilities statistics             
            vulnerabilitiesChartReady = True
            del parDashboards[vulnerabilitiesUUID]
            parRequestParams.AddParams('KLPPT_DASHBOARD', parDashboards)

            
    
def main():
    """ This sample shows how you can create a report and statistics chart """
    print (main.__doc__)
    
    #argument parsing
    parser = argparse.ArgumentParser(description='This module provides samples of KSC authorization')
    
    parser.add_argument('-l', action='store_true', help='Prints list of available reports and charts. Default action')
    parser.add_argument('-r', metavar='REPORT_ID', type = int, action='store', help='Generates report')
    parser.add_argument('-c', action='store_true', help='Generates 3 charts of the following types: 20 (Current state of the most anti-virus protection), 31 (State of the anti-viral protection deployment) and 50 (Amounts of vulnerability instances with different max. vulnerability severity during last week)')
             
    KlAkOAPI.ConnectionHelper.AddConnectionArgs(parser)
    
    args = parser.parse_args()

    # enumerating group is default action
    if args.l == False and args.r == None and args.c == False:
        args.l = True
    
    #connect to KSC server using basic auth by default
    server = KlAkOAPI.ConnectionHelper.ConnectFromCmdline(args)
    
    #use server object to construct objects wrapping KLOAPI calls 
    oReportManager = KlAkReportManager(server)
    
    # call samples depending on args
    if args.l:
        print('List of reports available on server:')
        arrReportsList = oReportManager.EnumReports().RetVal()
        for report in KlAkArray(arrReportsList):
            print ('* ID ' + str(report['RPT_ID']) + ': ' + report['RPT_DN'])
        print('List of statistics charts available in this sample (see KLOAPI for details):')
        for chart in KlAkArray(ChartList):
            print('*', chart)
        return
    
    if not args.r == None:
        Sample_GenerateReport(server, oReportManager, args.r)
    
    if args.c:   
        Sample_GetStatChart(server, oReportManager, args.c)
    
    
if __name__ == '__main__':
    main()