# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to put tags on hosts"""

import socket
import json
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray, paramParams, KlAkParamsEncoder
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.ListTags import KlAkListTags


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
    
def FindHosts(server):
    oHostGroup = KlAkHostGroup(server)
    nRootGroupId = oHostGroup.GroupIdGroups().RetVal()
    strAccessor = oHostGroup.FindHosts('(&(KLHST_WKS_HOSTNAME="*")(KLHST_WKS_GROUPID=' + str(nRootGroupId) + '))', ['KLHST_WKS_HOSTNAME', 'KLHST_WKS_DN'], [], {'KLGRP_FIND_FROM_CUR_VS_ONLY': True}, lMaxLifeTime = 100).OutPar('strAccessor')
    
    nStart = 0
    nStep = 100
    oChunkAccessor = KlAkChunkAccessor (server)    
    nCount = oChunkAccessor.GetItemsCount(strAccessor).RetVal()
    print('Found hosts count:', nCount)
    oResult = KlAkArray([])
    while nStart < nCount:
        oChunk = oChunkAccessor.GetItemsChunk(strAccessor, nStart, nStep)
        parHosts = oChunk.OutPar('pChunk')['KLCSP_ITERATOR_ARRAY']
        for oObj in parHosts:
            print('Found host: ' + oObj['KLHST_WKS_DN'])
            oResult.Add(oObj.GetValue('KLHST_WKS_HOSTNAME'))
        nStart += nStep    

    return oResult


def RunSample(server):
    oTagsControl = KlAkListTags(server, 'HostsTags')

    print('***** Tag Control *****')
    
    # enumerate all tags of the network list
    print('Enumerating existing tags...')

    oTags = oTagsControl.GetAllTags(None).RetVal()
    if oTags != None and len(oTags) > 0:
        for oObj in oTags:
           print('Tag: ', oObj)    
    print('Enumerating existing tags... Done.')

    # add a custom tag
    oTagsControl.AddTag('CustomTag', {})
    
    # rename it
    oTagsControl.RenameTag('CustomTag', 'NewCustomTag', {})
    
    # then delete
    oTagsControl.DeleteTags2(['NewCustomTag'], {})
    
    # enumerate tags of each host    
    oHostIds = FindHosts(server)
    if oHostIds == None or len(oHostIds) == 0:
        print('No hosts found to set tags (searched in Managed devices group)')
        return
        
    oTagArray = oTagsControl.GetTags(oHostIds, {}).RetVal()
    if oTagArray != None and len(oTagArray) > 0:
        for oTagEntry in oTagArray:
            oTagValues = oTagEntry['KLTAGS_TAGS']            
            strTags = ''
            for oTagValue in oTagValues:
                if strTags != '':
                    strTags += ', '
                strTags += oTagValue
            
            print('Tagged item id: ', oTagEntry['KLTAGS_ITEM_ID'], ', Tags set for this id: ', strTags)
    
    
    # set 'CustomTag' for host
    oTagsControl.AddTag('CustomTag', {})
    
    oTagArrayItem = KlAkParams({'KLTAGS_VALUE': 'CustomTag', 'KLTAGS_SET': True})
    oHostsArrayItem = KlAkParams({'KLTAGS_ITEM_ID': oHostIds[0], 'KLTAGS_TAGS': [paramParams(oTagArrayItem)]})    
    oHostsArray = [ paramParams(oHostsArrayItem) ] 
    
    oTagsControl.SetTags(oHostsArray, {'KLTAGS_FULL_REPLACE': False})

    
def main():
    """ This sample shows how you can put tags on hosts """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    RunSample(server)

    
if __name__ == '__main__':
    main()