# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to view licenses"""

import socket
import datetime
from sys import platform
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.VServers import KlAkVServers
from KlAkOAPI.LicenseKeys import KlAkLicenseKeys
from KlAkOAPI.GroupSyncIterator import KlAkGroupSyncIterator

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

def SubscriptionEndDateTypeAsString(nEndDateType):
    if nEndDateType == 0:
        return 'Not Defined'
    elif nEndDateType == 1:
        return 'Unlimited'
    elif nEndDateType == 2:
        return 'Limited'
    elif nEndDateType == 3:
        return 'Paused'
    return 'Unknown (' + nEndDateType + ')'


def SubscriptionStateAsString(nSubscrState):
    if nSubscrState == 0:
        return 'Active'
    elif nSubscrState == 1:
        return 'Paused'
    elif nSubscrState == 2:
        return 'Soft Cancelled'
    elif nSubscrState == 3:
        return 'Hard Cancelled'
    return 'Unknown (' + nSubscrState + ')'


def FindActiveLicense(server):
    print('Local time is ' + datetime.datetime.now().isoformat())

    oLicenses = KlAkLicenseKeys(server)

    # Enumerate keys
    oFileds2Return = ['KLLIC_APP_ID', 'KLLIC_PROD_SUITE_ID', 'KLLIC_LIMIT_DATE', 'KLLIC_SERIAL', 'KLLIC_PROD_NAME', 'KLLIC_KEY_TYPE', 'KLLIC_MAJ_VER', 'KLLIC_LICENSE_PERIOD', 'KLLIC_LIC_COUNT', 'KLLICSRV_KEY_INSTALLED', 'KLLIC_LICINFO', 'KLLIC_SUPPORT_INFO', 'KLLIC_CUSTOMER_INFO', 'KLLIC_LICTYPE_IS_SUBSCRIPTION', 'KLLIC_SUBSCRINFO_ENDDATE', 'KLLIC_SUBSCRINFO_ENDDATETYPE', 'KLLIC_SUBSCRINFO_GRACETERM', 'KLLIC_SUBSCRINFO_PROVIDERURL', 'KLLIC_SUBSCRINFO_STATE']

    oChunkAccessor = oLicenses.EnumKeys(oFileds2Return, [], {}, lTimeoutSec = 60 * 60)
    lKeyCount = oChunkAccessor.OutPar('lKeyCount')
    wstrIterator = oChunkAccessor.OutPar('wstrIterator')

    bFound = False
    nStep = 50
    oGroupSyncIterator = KlAkGroupSyncIterator(server)
    while True:
        enumObj = oGroupSyncIterator.GetNextItems(wstrIterator, nStep)
        pData = enumObj.OutPar('pData')
        for oObj in pData['KLCSP_ITERATOR_ARRAY']:
            bFound = (oObj['KLLIC_LIMIT_DATE'] > datetime.datetime.now())
            
            print('KLLIC_APP_ID:', oObj['KLLIC_APP_ID'])
            print('KLLIC_PROD_SUITE_ID:', oObj['KLLIC_PROD_SUITE_ID'])
            print('KLLIC_LIMIT_DATE: ', oObj['KLLIC_LIMIT_DATE'])
            print('KLLIC_SERIAL: ', oObj['KLLIC_SERIAL'])
            print('KLLIC_PROD_NAME:', oObj['KLLIC_PROD_NAME'])
            print('KLLIC_KEY_TYPE:', oObj['KLLIC_KEY_TYPE'])
            print('KLLIC_LICENSE_PERIOD:', oObj['KLLIC_LICENSE_PERIOD'])
            print('KLLIC_LIC_COUNT:', oObj['KLLIC_LIC_COUNT'])
            print('KLLICSRV_KEY_INSTALLED:', oObj['KLLICSRV_KEY_INSTALLED'])
            print('KLLIC_LICINFO:', oObj['KLLIC_LICINFO'])
            print('KLLIC_SUPPORT_INFO:', oObj['KLLIC_SUPPORT_INFO'])
            print('KLLIC_CUSTOMER_INFO:', oObj['KLLIC_CUSTOMER_INFO'])
            bIsSubscription = oObj['KLLIC_LICTYPE_IS_SUBSCRIPTION']
            print('KLLIC_LICTYPE_IS_SUBSCRIPTION:', bIsSubscription)
            if bIsSubscription:
                print('KLLIC_SUBSCRINFO_ENDDATE:', oObj['KLLIC_SUBSCRINFO_ENDDATE'])
                print('KLLIC_SUBSCRINFO_ENDDATETYPE:', SubscriptionEndDateTypeAsString(oObj['KLLIC_SUBSCRINFO_ENDDATETYPE']))
                print('KLLIC_SUBSCRINFO_GRACETERM:', oObj['KLLIC_SUBSCRINFO_GRACETERM'] + ' days')
                print('KLLIC_SUBSCRINFO_PROVIDERURL:', oObj['KLLIC_SUBSCRINFO_PROVIDERURL'])
                strSubscrState = SubscriptionStateAsString(oObj['KLLIC_SUBSCRINFO_STATE'])
                print('KLLIC_SUBSCRINFO_STATE:', strSubscrState)
                bFound = bFound and strSubscrState == 'Active'

            print('License is active:', bFound)
            print('______________________')

        if enumObj.OutPar('bEOF') == True:
            break
            
    oGroupSyncIterator.ReleaseIterator(wstrIterator)
    return bFound


def EnumVServersAndTheirLicenses(server):
    oVServers = KlAkVServers(server)
    oVServerCollection = oVServers.GetVServers(-1).RetVal()
    
    for oVServerInfo in oVServerCollection:
        strVServerDN = oVServerInfo['KLVSRV_DN']		
        print('Enumerating licenses of VServer "' + strVServerDN + '"')
        vserver = KlAkAdmServer.Create(server_url, username, password, verify = SSLVerifyCert, vserver = strVServerDN)
        if not FindActiveLicense(vserver):
            print('FAILURE! There''s no active license on VServer "' + strVServerDN + '"')

    
def main():
    """ This sample shows how you can see licenses in use """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = KlAkAdmServer.Create(server_url, username, password, verify = SSLVerifyCert)

    print('Main server licenses:')
    if not FindActiveLicense(server):
        print('FAILURE! There''s no active license on server')
        
    EnumVServersAndTheirLicenses(server)

    
if __name__ == '__main__':
    main()