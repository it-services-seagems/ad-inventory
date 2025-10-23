# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to view some statistics"""

import socket
import uuid
import time
import base64
import os
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams, dateTimeToStr
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.ReportManager import KlAkReportManager
import KlAkOAPI.ReportManager
import KlAkOAPI.Params
import KlAkOAPI.HostGroup

strResultFolderName = 'results'  


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
    
def AcquireStatistics(oReportManager):

    oQuery = KlAkParams({})
    oQuery.AddParams('KLSTS_Administration', {})
    oQuery.AddParams('KLSTS_Deployment', {})
    oQuery.AddParams('KLSTS_Events', {})
    oQuery.AddParams('KLSTS_FullScan', {})
    oQuery.AddParams('KLSTS_Protection', {})
    oQuery.AddParams('KLSTS_Updates', {})

    oQueryDsh_AvBases = KlAkParams({'KLRPT_DSH_TYPE': 22})
    uuidAvBases = str(uuid.uuid4())

    oQueryDsh_Viract = KlAkParams({'KLRPT_DSH_TYPE': 2, 'KLPPT_StatPeriodInSec': 30*24*3600})
    uuidViract = str(uuid.uuid4())

    oQueryDsh = KlAkParams({uuidAvBases: paramParams(oQueryDsh_AvBases), uuidViract: paramParams(oQueryDsh_Viract)})
    oQuery.AddParams('KLPPT_DASHBOARD', oQueryDsh)
        
    print('AcquireStatisticsData started')
    
    # gathering statistics needs time, one dash can be done earlier than others, so check progress by timer
    while True:
        if len(oQuery) == 0:
            break
            
        # request statistics for dashboards that are not ready yet by this time
        strRequestId = oReportManager.RequestStatisticsData(oQuery).OutPar('strRequestId')

        # wait a bit while statistics is collected and prepared
        time.sleep(5)

        # get result
        pResultData = oReportManager.GetStatisticsData(strRequestId).OutPar('pResultData')
        
        if pResultData == None:
            continue
            
        if 'KLPPT_DASHBOARD' in pResultData:            
            # statistics is ready, now make charts with recieved data
            pDashboards = pResultData['KLPPT_DASHBOARD']
            
            # create folder for result
            if not os.path.exists(strResultFolderName):
                os.makedirs(strResultFolderName)
 
            if uuidAvBases in pDashboards:
                # compose params with statistics data for deployment chart
                CreateAvBasesChart(oReportManager, pDashboards[uuidAvBases], os.path.join(strResultFolderName, 'dash_av_bases.png'))                    
                del oQueryDsh[uuidAvBases]
                
            if uuidViract in pDashboards:
                # compose params with statistics data for deployment chart
                CreateViractChart(oReportManager, pDashboards[uuidViract], os.path.join(strResultFolderName, 'dash_viract.png'))
                del oQueryDsh[uuidViract]  
                
            # recompose data for furher request if some other statistics are not ready yet - no need re-request deployment statistics
            if len(oQueryDsh) == 0:
                del oQuery['KLPPT_DASHBOARD']
            else:
                oQuery.AddParams('KLPPT_DASHBOARD', oQueryDsh)
        
        # verbalize statistics results
        if 'KLSTS_Administration' in pResultData:
            ParseAdministrationStatus(pResultData['KLSTS_Administration'])
            del oQuery['KLSTS_Administration']
        
        if 'KLSTS_Deployment' in pResultData:
            ParseDeploymentStatus(pResultData['KLSTS_Deployment'])
            del oQuery['KLSTS_Deployment']
                
        if 'KLSTS_Events' in pResultData:
            ParseEventsStatus(pResultData['KLSTS_Events'])
            del oQuery['KLSTS_Events']
        
        if 'KLSTS_FullScan' in pResultData:
            ParseFullScanStatus(pResultData['KLSTS_FullScan'])
            del oQuery['KLSTS_FullScan']
        
        if 'KLSTS_Protection' in pResultData:
            ParseProtectionStatus(pResultData['KLSTS_Protection'])
            del oQuery['KLSTS_Protection']
        
        if 'KLSTS_Updates' in pResultData:
            ParseUpdatesStatus(pResultData['KLSTS_Updates'])
            del oQuery['KLSTS_Updates']

            
    print("AcquireStatisticsData returned")

def CreateAvBasesChart(oReportManager, oDsh_AvBases, strDshFilename):    
    oDsh_Data = KlAkParams({'data': [oDsh_AvBases.GetValue('nCountActual'), oDsh_AvBases.GetValue('nCountDay'), oDsh_AvBases.GetValue('nCount3Days'), oDsh_AvBases.GetValue('nCount7Days'), oDsh_AvBases.GetValue('nCountOld')], 'name': 'AvBases'})
    oDsh_Descr = KlAkParams({})
    oDsh_Descr.AddArray('KLRPT_CHART_DATA', [paramParams(oDsh_Data)])
    oDsh_Descr.AddString('KLRPT_CHART_DATA_DESC', 'Distribution of AV bases versions on hosts')
    oDsh_Descr.AddString('KLRPT_CHART_LGND_DESC', 'number of installed products with:')
    oDsh_Descr.AddArray('KLRPT_CHART_SERIES', ['actual bases', 'inactual bases released last 24 hours', 'inactual bases released last 3 days', 'inactual bases released last 7 days', 'inactual bases released more than 7 days ago'])
    oDsh_Descr.AddBool('KLRPT_CHART_PIE', True)
        
    # create chart and download a result file
    res = oReportManager.CreateChartPNG(oDsh_Descr, {'RPT_CHART_WIDTH': 600, 'RPT_CHART_HEIGHT': 600})
    with open(strDshFilename, 'wb') as f:
        packet = base64.b64decode(res.OutPar('pPngData'))
        f.write(packet)
    print('AvBases chart is ready:', strDshFilename)

def CreateViractChart(oReportManager, oDsh_Viract, strDshFilename):
    oDsh_Data = KlAkArray([])
    for oObj in oDsh_Viract['DSHT_DATA']:
        oDsh_DataItem = KlAkParams({'data': [oObj.GetValue('nCount')]})
        oDsh_DataItem.AddString('name', dateTimeToStr(oObj['tmFinish']))
        oDsh_Data.AddParams(oDsh_DataItem)
   
    oDsh_Descr = KlAkParams({})
    oDsh_Descr.AddArray('KLRPT_CHART_DATA', oDsh_Data)
    oDsh_Descr.AddString('KLRPT_CHART_DATA_DESC', 'Distribution of virus activity in time')
    oDsh_Descr.AddString('KLRPT_CHART_LGND_DESC', 'number of installed products with:')
    oDsh_Descr.AddArray('KLRPT_CHART_SERIES', ['number of threat detections during the interval'])
    oDsh_Descr.AddBool('KLRPT_CHART_PIE', False)
        
    # create chart and download a result file
    res = oReportManager.CreateChartPNG(oDsh_Descr, {'RPT_CHART_WIDTH': 600, 'RPT_CHART_HEIGHT': 600})
    with open(strDshFilename, 'wb') as f:
        packet = base64.b64decode(res.OutPar('pPngData'))
        f.write(packet)
    print('Viract chart is ready:', strDshFilename)
                
                
def ParseAdministrationStatus(parAdministrationStatus):
    print('-- Administration: --')
    status = parAdministrationStatus['KLSTS_Par_Status']
    if status == 0:
        print('Status: Ok')
    elif status == 1:
        print('Status: Informational')
    elif status == 2:
        print('Status: Warning')    
    elif status == 3:
        print('Status: Critical')

    mask = parAdministrationStatus['KLSTS_Par_StatusReasonMask']
    if mask == 0:
        print(parAdministrationStatus['KLSTS_Par_Adm_FoundHstCnt'], 'hosts discovered,', parAdministrationStatus['KLSTS_Par_Adm_GrpHstCnt'], 'hosts located in', parAdministrationStatus['KLSTS_Par_Adm_GrpCnt'], 'administration groups.')
    if mask & 1:
        print(parAdministrationStatus['KLSTS_Par_Adm_NotConnectedLongTimeCnt'], 'hosts have not connected to the KSC server for a long time (host status reason bit 256 is set).')
    if mask & 2:
        print('There are', parAdministrationStatus['KLSTS_Par_Adm_ControlLostCnt'], 'hosts having non-Ok status because of "out of control" reason (host status reason bit 1 is set).')
    if mask & 4:
        print('Netbios names conflict detected.')
    if mask & 8:
        print('There are', parAdministrationStatus['KLSTS_Par_Adm_NagInUnassigned'], 'hosts with Network Agent installed not placed to managed administration groups')
    if mask & 16:
        print('There is patch to update SC-server which expecting approval on installation')

          
def ParseDeploymentStatus(parDeploymentStatus):
    print('-- Deployment: --')
    status = parDeploymentStatus['KLSTS_Par_Status']
    if status == 0:
        print('Status: Ok')
    elif status == 1:
        print('Status: Informational')
    elif status == 2:
        print('Status: Warning')    
    elif status == 3:
        print('Status: Critical')

    mask = parDeploymentStatus['KLSTS_Par_StatusReasonMask']
    if mask == 0:
        print('All the hosts located in the managed administration groups have Kaspersky anti-virus product installed')
    if mask & 1:
        print('There are', parDeploymentStatus['KLSTS_Par_Dpl_HostsInGroups'],'hosts located in the managed administration groups, but only', parDeploymentStatus['KLSTS_Par_Dpl_HostsWithAVP'],'of them have Kaspersky anti-virus product installed')
    if mask & 2:
        print('Remote installation task', parDeploymentStatus['KLSTS_Par_Dpl_RITaskName'],'is in progress, completion percent is', parDeploymentStatus['KLSTS_Par_Dpl_RITaskPercent'])
    if mask & 4:
        print('Remote installation task', parDeploymentStatus['KLSTS_Par_Dpl_RITaskName'],'failed on', parDeploymentStatus['KLSTS_Par_Dpl_RITaskFailedCnt'], 'hosts (succeeded on', parDeploymentStatus['KLSTS_Par_Dpl_RITaskOkCnt'], 'hosts, reboot required on', parDeploymentStatus['KLSTS_Par_Dpl_RITaskNeedRbtCnt'], 'hosts). Status can be reset')
    if mask & 8:
        print('Remote installation task required reboot on', parDeploymentStatus['KLSTS_Par_Dpl_RITaskNeedRbtCnt'],'hosts (succeeded on', parDeploymentStatus['KLSTS_Par_Dpl_RITaskOkCnt'],'hosts). Status can be reset')
    if mask & 16:
        print('License', parDeploymentStatus['KLSTS_Par_Dpl_LicExparingSerial'], 'expires on', parDeploymentStatus['KLSTS_Par_Dpl_LicExparingCnt'],'hosts in', parDeploymentStatus['KLSTS_Par_Dpl_LicExparingDays'],'days')
    if mask & 32:
        print('License', parDeploymentStatus['KLSTS_Par_Dpl_LicExparedSerial'], 'expired on', parDeploymentStatus['KLSTS_Par_Dpl_LicExparedCnt'],'hosts')
             
        
def ParseEventsStatus(parEventsStatus):
    print('-- Events: --')
    status = parEventsStatus['KLSTS_Par_Status']
    if status == 0:
        print('Status: Ok')
    elif status == 1:
        print('Status: Informational')
    elif status == 2:
        print('Status: Warning')    
    elif status == 3:
        print('Status: Critical')

    mask = parEventsStatus['KLSTS_Par_StatusReasonMask']
    if mask == 0:
        print('No new critical events or errors found')
    if mask & 1:
        print('There are', parEventsStatus['KLSTS_Par_Ev_CriticalSrvEventsCnt'], 'new critical events registered on the server (starting from the moment when the status was reset). Status can be reset')
    if mask & 2:
        print('Administration server''s task', parEventsStatus['KLSTS_Par_Ev_FailedSrvTskName'], 'failed (starting from the moment when the status was reset). Status can be reset')
    if mask & 4:
        print(parEventsStatus['KLSTS_Par_Ev_UserRequestsCnt'], 'new user requests raised')    
    if mask & 8:
        print('There are',parEventsStatus['KLSTS_Par_Ev_ErrorSrvEventsCnt'],'new error events registered on the server(starting from the moment when the status was reset). Status can be reset.')   
    if mask & 16:
        print(parEventsStatus['KLSTS_Par_Ev_WuaDataObsoleteCnt'], 'computers in administration groups have not searched for Windows updates for long time (based on computer status).')    
    if mask & 32:
        print('There are', parEventsStatus['KLSTS_Par_Ev_VapmEulaUpdatesCnt'], 'software updates to be installed which have EULA to be accepted first')    
    if mask & 64:
        print('There are', parEventsStatus['KLSTS_Par_Ev_BadStatusHostsCnt'], 'new hosts which status is not OK (other reasons, not analyzed in other statuses).')    
    if mask & 128:
        print('New APS files were appeared after last notice')    
    if mask & 512:
        print('There are applicable patches for managed KL products that are not yet approved by administrator')        
    if mask & 1024:
        print('There are applicable patches for managed KL products that have KSN agreements not yet accepted by administrator')        
    if mask & 2048:
        print('There are applicable patches for managed KL products that have EULAs not yet accepted by administrator')        
    if mask & 4096:
        print('There are installed revoked patches which are not yet declined by administrator')        
    if mask & 8192:
        print('Kaspersky Security Center requires reboot on reason', parEventsStatus['KLSTS_Par_Ev_AdmSrvRbtRsn'])        
    if mask & 16384:
        print(parEventsStatus['KLSTS_Par_Ev_NewVersionsCnt'], 'new versions of already used products available to download, including', parEventsStatus['KLSTS_Par_Ev_NewKscVersionsCnt'], 'KSC components')
    if mask & 32768:
        print(parEventsStatus['KLSTS_Par_Ev_NewProductsCnt'], 'new product distributives available to download')        
    if mask & 65536:
        print(parEventsStatus['c_sts_Par_Ev_RequiredPluginsCnt'], 'KSC MMC-console plugins must be upgraded to manage the applicable or installed seamless updates')        
    if mask & 131072:
        print('There are mobile EULAs that are not yet accepted by administrator.')        

def ParseFullScanStatus(parFullScanStatus):
    print('-- Full scan: --')
    status = parFullScanStatus['KLSTS_Par_Status']
    if status == 0:
        print('Status: Ok')
    elif status == 1:
        print('Status: Informational')
    elif status == 2:
        print('Status: Warning')    
    elif status == 3:
        print('Status: Critical')

    mask = parFullScanStatus['KLSTS_Par_StatusReasonMask']
    if mask == 0:
        print('Fullscan completed on all the managed hosts')
    if mask & 1:
        print('Fullscan not performed too long on N', parFullScanStatus['KLSTS_Par_Scn_NotScannedLatelyCnt'], 'computers')

def ParseUpdatesStatus(parUpdatesStatus):
    print('-- Updates: --')
    status = parUpdatesStatus['KLSTS_Par_Status']
    if status == 0:
        print('Status: Ok')
    elif status == 1:
        print('Status: Informational')
    elif status == 2:
        print('Status: Warning')    
    elif status == 3:
        print('Status: Critical')

    mask = parUpdatesStatus['KLSTS_Par_StatusReasonMask']
    if mask == 0:
        print('Updates are working properly, KSC server update task succeeded at time', parUpdatesStatus['KLSTS_Par_Upd_LastSrvUpdateTime'])
    if mask & 1:
        print('KSC server has not updated for a long time; last update time is:', parUpdatesStatus['KLSTS_Par_Upd_LastSrvUpdateTime'])
    if mask & 2:
        print(parUpdatesStatus['KLSTS_Par_Upd_NotUpdatesCnt'], 'managed hosts have not updated for a long time')
    if mask & 4:
        print('KSC server update task in progress, completion percent', parUpdatesStatus['KLSTS_Par_Upd_SrvCompletedPercent'])    


def ParseProtectionStatus(parProtectionStatus):
    print('-- Protection status: --')
    status = parProtectionStatus['KLSTS_Par_Status']
    if status == 0:
        print('Status: Ok')
    elif status == 1:
        print('Status: Informational')
    elif status == 2:
        print('Status: Warning')    
    elif status == 3:
        print('Status: Critical')

    mask = parProtectionStatus['KLSTS_Par_StatusReasonMask']
    if mask == 0:
        print('Runtime protection work on all the computers in the administration groups')
    if mask & 1:
        print('Antivirus software is not running on', parProtectionStatus['KLSTS_Par_Prt_AvpNotRunningCnt'], 'computers in the administration groups')
    if mask & 2:
        print('Runtime protection doesn''t work on', parProtectionStatus['KLSTS_Par_Prt_RtpNotRunningCnt'], 'computers in the administration groups.')
    if mask & 4:
        print('Runtime protection level differs from the level set by administrator on', parProtectionStatus['KLSTS_Par_Prt_RtpLevelChangedCnt'], 'computers in the administration groups')    
    if mask & 8:
        print('Uncured objects found on', parProtectionStatus['KLSTS_Par_Prt_NoncuresHstCnt'], 'computers in the administration groups')   
    if mask & 16:
        print('Too many viruses found on', parProtectionStatus['KLSTS_Par_Prt_TooManyThreadsCnt'], 'computers in the administration groups')    
    if mask & 32:
        print('Virus outbreak occured')    
    if mask & 64:
        print('Vulnerabilities found')    
    if mask & 128:
        print('Encryption faults caused hosts to change protection status ')    
    if mask & 256:
        print(parProtectionStatus['KLSTS_Par_Prt_VulnerabileHostsCnt'], 'hosts found which has non-Ok status because of vulnerabilities found ')    
    if mask & 512:
        print('Fullscan not performed too long on', parProtectionStatus['KLSTS_Par_Prt_NotScannedLatelyCnt'], 'computers')        

def main():
    """ This sample shows how you can view statistics """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    AcquireStatistics(KlAkReportManager(server))
    
    
if __name__ == '__main__':
    main()