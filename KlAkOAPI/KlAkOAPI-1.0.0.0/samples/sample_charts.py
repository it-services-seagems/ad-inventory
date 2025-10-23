# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create statistics charts"""

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
from KlAkOAPI.ReportManager import KlAkReportManager
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
                    
def RGB(r, g, b):
    """ Transforms RGB values to int, sample of use: RGB(0xFF, 0x88, 0x88). Used in Sample_GetStatChart """
    return r + (g << 8) + (b << 16)       
   
ChartList = ['(Diagram) Current state of the most anti-virus protection (number of hosts with status Critical, Warning and OK). ',  # type 20
'(Diagram) State of the anti-viral protection deployment (number of hosts with nagent and anti-virus, nagent only, nothing). ', # type 31, 
'(Histogram) Amounts of vulnerability instances with different max. vulnerability severity (critical, high, warning, none) during some time intervals. ', # type 50
]   
   
def GetStatCharts(server, oReportManager):
    """ Requests for statistics and download the result chart file """
    print('Creating following statistics charts for root group: \n* Current state of the most anti-virus protection (type 20), \n* State of the anti-viral protection deployment (type 31) and \n* Amounts of vulnerability instances with different max. vulnerability severity during last week (type 50, where time interval is set to last week)')
    
    # get root group id
    oHostGroup = KlAkHostGroup(server)
    nGroupId = oHostGroup.GroupIdGroups().RetVal()
    
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
    parDashboards.AddParams(vulnerabilitiesUUID, {'KLRPT_DSH_TYPE': 50, 'KLPPT_StatFinishTime': datetime.datetime.now(), 'KLPPT_StatPeriodInSec': 60 * 60 * 24 * 7})  # time period: 7 days ago from now
	
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

        # create folder for result
        if not os.path.exists(strResultFolder):
            os.makedirs(strResultFolder)

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
    """ This sample shows how you can create statistics charts """
    print (main.__doc__)
    
    #connect to KSC server using basic auth by default
    server = GetServer()
    
    #use server object to construct objects wrapping KLOAPI calls 
    oReportManager = KlAkReportManager(server)
    
    # create charts
    GetStatCharts(server, oReportManager)
    
    
if __name__ == '__main__':
    main()