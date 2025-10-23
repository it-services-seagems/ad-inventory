# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to deal with KSC group structure"""

import sys
import socket
import datetime
from sys import platform
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.Params import KlAkParams, dateToStr, dateTimeToStr
from KlAkOAPI.Base import MillisecondsToSeconds
from KlAkOAPI.Error import KlAkError
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.AsyncActionStateChecker import KlAkAsyncActionStateChecker
    

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
        
def FindGroups(oHostGroup, server, sFilter):
    """ Searches KSC groups that require search filter """  
    print('Searching groups that require filter "'+ sFilter+ '":')     
     
    res = oHostGroup.FindGroups(sFilter, vecFieldsToReturn=['id', 'name', 'grp_full_name', 'parentId', 'level'], vecFieldsToOrder = [], pParams = {}, lMaxLifeTime=100)
    print('Found ' + str(res.RetVal()) + ' groups:')    
    strAccessor = res.OutPar('strAccessor')
        
    # chunkAccessor object allows iteration over search results
    oChunkAccessor = KlAkChunkAccessor (server)
    nItemsCount = oChunkAccessor.GetItemsCount(strAccessor).RetVal()
    nStart = 0
    nStep = 20000
    while nStart < nItemsCount:        
        oChunk = oChunkAccessor.GetItemsChunk(strAccessor, nStart, nStep).OutPar('pChunk')
        for parGroup in oChunk['KLCSP_ITERATOR_ARRAY']:
            print (parGroup['grp_full_name'])
        nStart += nStep

def RemoveGroup(oHostGroup, server, nGroupId):
    """ Removing a group """
    print('Removing group')
    
    # retrieve group name from id
    parGroupInfo = oHostGroup.GetGroupInfo(nGroupId).RetVal()
    print('Group to remove is: ' + parGroupInfo['grp_full_name'])
    
    # check for root group
    if nGroupId == oHostGroup.GroupIdGroups().RetVal():
       print('Cannot delete root group, please use another group id')
       return
    
    # remove group asynchronously
    strActionGuid = oHostGroup.RemoveGroup(nGroup = nGroupId, nFlags = 1).OutPar('strActionGuid')
    
    # check for result of asynchronous action
    oAsyncActionStateChecker = KlAkAsyncActionStateChecker (server)
    while True:
        res = oAsyncActionStateChecker.CheckActionState(strActionGuid)
        if res.OutPar('bFinalized'):
            if res.OutPar('bSuccededFinalized'):
                # got asynchronous result: success 
                print ('Group deleted successfully')
            else:
                # got asynchronous result: some error occurred
                oErrDescription = KlAkParams(res.OutPar('pStateData'))
                print('Cannot delete group:', oErrDescription['GNRL_EA_DESCRIPTION'], '(error code ' + str(oErrDescription['KLBLAG_ERROR_INFO']['KLBLAG_ERROR_CODE']) + ')')
            return
        else:
            # asynchronous result is not ready yet - need to wait for lNextCheckDelay milliseconds
            time.sleep(MillisecondsToSeconds(res.OutPar('lNextCheckDelay')))

        
def AddGroup(oHostGroup, sGroupName, nParentGroupId):
    """ Adds KSC group """
    parGroupInfo = oHostGroup.GetGroupInfo(nParentGroupId).RetVal()    
    print('Adding subgroup ' + sGroupName + ' into "'+ parGroupInfo['grp_full_name'] +'" group')
    
    # check if group already exists
    nGroupsFoundCount = oHostGroup.FindGroups('(name="' + sGroupName + '")', ['id'], [], {}, 100).RetVal()
    if nGroupsFoundCount > 0:
        print ('Group ' + sGroupName + ' already exists')
        return
    
    # add new group    
    nGroupId = oHostGroup.AddGroup({'name': sGroupName, 'parentId': nParentGroupId}).RetVal()  
    print('Group added successfully')
    return nGroupId
    
def main():
    """ This sample shows how you can search groups with some filter string, create and delete group """
    print (main.__doc__)
    
    # connect to KSC server using basic auth by default
    server = GetServer()
    
    # use server object to construct objects wrapping KLOAPI calls 
    oHostGroup = KlAkHostGroup(server)
    
    timeCurrentTime = datetime.datetime.now()
    strCurrentTime = dateTimeToStr(timeCurrentTime).replace("-", "_").replace(":", "_")
    
    # create new group
    nRootGroupID = oHostGroup.GroupIdGroups().RetVal()
    nNewGroupId = AddGroup(oHostGroup, 'TestGroup-' + strCurrentTime, nRootGroupID)

    # Some samples of filter that can be used in FindGroups call are below:
    # groups named "Comput*":
    #sFilter = '(name="Comput*")'
    # groups created before 31 march 2020:
    #sFilter = '(creationDate<"2020-03-31T00:00:00Z")'
    # groups with one or more dvices with status 'Critical':
    #sFilter = '(KLGRP_CHLDHST_CNT_CRT >= 1)'
    # groups where amount of computers >= 100 (not including computers in subgroups):
    #sFilter = '(KLGRP_CHLDHST_CNT >= 100)'
    # large groups created recently:
    #sFilter = '(&(KLGRP_CHLDHST_CNT >= 1000)(creationDate>"2020-03-31T19:00:00Z"))'
    # all groups:
    #sFilter = ''
    
    FindGroups(oHostGroup, server, '(name="*-' + strCurrentTime + '")')
    
    FindGroups(oHostGroup, server, '(creationDate>="' + dateToStr(timeCurrentTime.date()) +'")')
    
    FindGroups(oHostGroup, server, '(KLGRP_CHLDHST_CNT_CRT<1)')

    # remove group
    RemoveGroup(oHostGroup, server, nNewGroupId)
    
if __name__ == '__main__':
    main()