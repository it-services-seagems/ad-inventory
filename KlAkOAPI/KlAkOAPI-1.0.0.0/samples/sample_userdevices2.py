# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to view user's devices"""

import socket
import uuid
import time
import base64
from KlAkOAPI.Params import binToStr
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.UserDevicesApi import KlAkUserDevicesApi
from KlAkOAPI.SrvView import KlAkSrvView


def GetServer():
    """Connects to KSC server"""
    # server details - connect to server installed on current machine, use default port
    server_address = socket.getfqdn()
    server_port = 13299
    server_url = 'https://' + server_address + ':' + str(server_port)

    # account for connecting server - user 'klakoapi_test' with password 'test1234!' should be created on KSC server in advance
    username = 'klakoapi_test'
    password = 'test1234!'
    
    SSLVerifyCert = 'C:\\ProgramData\\KasperskyLab\\adminkit\\1093\\cert\\klserver.cer'

    # create server object
    server = KlAkAdmServer.Create(server_url, username, password, verify = SSLVerifyCert)
    
    return server
    
def FindUser(server, strUsername):
    if strUsername == '':
        return None
        
    oSrvView = KlAkSrvView(server)
    wstrIteratorId = oSrvView.ResetIterator('GlobalUsersListSrvViewName', '(&(ul_wstrDisplayName=\"' + strUsername + '\")(ul_nVServer = 0))', ['ul_binId', 'ul_llTrusteeId', 'ul_wstrDisplayName'], [], {}, lifetimeSec = 60*5).OutPar('wstrIteratorId')
    binId = None
    if oSrvView.GetRecordCount(wstrIteratorId).RetVal()  > 0:
        pRecords = oSrvView.GetRecordRange(wstrIteratorId, 0, 1).OutPar('pRecords')
        pRecordsArray = pRecords['KLCSP_ITERATOR_ARRAY']
        if pRecordsArray != None and len(pRecordsArray) > 0:
            binId = pRecordsArray[0]['ul_binId']        
    oSrvView.ReleaseIterator(wstrIteratorId)
    
    if binId == None:
        print('User', strUsername, 'not found')
        return
        
    return binToStr(binId)
        
        
def Start(server, oUserDevices):
    strUserId = FindUser(server, '')
    if strUserId == None:
        print('Searching devices of current user')

    print('***** SSP Login Checking *****')
    oUserDevices.SspLoginAllowed()
    print('OK')

    print('***** Device List *****')	
    oDevices = oUserDevices.GetDevices(strUserId).RetVal()
    if oDevices != None and len(oDevices) > 0:
        for oObj in oDevices:
            print('Device id: ', oObj['KLMDM_DEVICE_ID'])
            print('Device model: ', oObj['KLMDM_DEVICE_MODEL'])
            print('Device OS: ', oObj['KLMDM_DEVICE_OS'])
            print('Device friendly name: ', oObj['KLMDM_DEVICE_FRIENDLY_NAME'])
            print('Device phone number: ', oObj['KLMDM_DEVICE_PHONE_NUMBER'])		   
            print('Device alias: ', oObj['KLMDM_DEVICE_ALIAS'])
            if 'KLMDM_DEVICE_MDM_PROTOCOL' in oObj:
                print('Device MDM protocol: ', oObj['KLMDM_DEVICE_MDM_PROTOCOL'])		   
            print('--')

    print('***** Package List *****')

    oEnrPkgs = oUserDevices.GetEnrollmentPackages(strUserId).RetVal()
    if oEnrPkgs != None and len(oEnrPkgs) > 0:
        for oObj in oEnrPkgs:
            print('Package id: ', oObj['KLMDM_ENR_PKG_ID'])
            print('Package MDM protocol: ', oObj['KLMDM_ENR_PKG_MDM_PROTOCOLS'])
            print('Package delivery type: ', oObj['KLMDM_ENR_PKG_DELIVERY_TYPE'])
            print('Package state: ', oObj['KLMDM_ENR_PKG_STATE'])
            print('Package URL: ', oObj['KLMDM_ENR_PKG_UNIFIED_URL'])
            print('Package live time: ', oObj['KLMDM_ENR_PKG_LIVE_TIME'])
            print('Remaining time to download: ', oObj['KLMDM_ENR_PKG_REMAINING_TIME'])		   

            print('--')

    print('***** Calling GetMobileAgentSettingStorageData() *****')
    oSsData = oUserDevices.GetMobileAgentSettingStorageData(1, '.MainSection').RetVal() # 1 is nDeviceId
    print(oSsData)
    print('***** OK *****')


    print('***** Multitenancy Servers Info *****')
	
    strMtncSrvInfoStrId = None
    oMtncSrvsInfo = oUserDevices.GetMultitenancyServersInfo(1).RetVal() # 1 means IOSMDM protocol
    if oMtncSrvsInfo != None and len(oMtncSrvsInfo) > 0:
        strMtncSrvInfoStrId = oMtncSrvsInfo[0]['MTNC_SRV_INFO_STR_ID']
        for oObj in oMtncSrvsInfo:
            print('Multitenancy server string ID: ', oObj['MTNC_SRV_INFO_STR_ID'])
            print('Multitenancy server protocol ID: ', oObj['MTNC_SRV_INFO_PROT_ID'])
            print('Display name of the host where installed multitenancy server: ', oObj['MTNC_SRV_INFO_HOST_DN'])
            print('Multitenancy server display name: ', oObj['MTNC_SRV_INFO_PROD_DN'])
            print('Human readable version of the multitenancy server: ', oObj['MTNC_SRV_INFO_PROD_DV'])
            print('--')

    if strMtncSrvInfoStrId != None:
        oSettings = oUserDevices.GetMultitenancyServerSettings(strMtncSrvInfoStrId).RetVal()
        print('Mtnc settings:', oSettings)


def main():
    """ This sample shows how you can view user's devices """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oUserDevicesApi = KlAkUserDevicesApi(server)
    Start(server, oUserDevicesApi)

    
if __name__ == '__main__':
    main()