# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to deal with KSC group structure.
KlAkOAPI package is a wrapper library for interacting Kaspersky Security Center (aka KSC) server with KSC Open API
For detailed description of KSC Open API protocol please refer to KLOAPI documentation pages
"""

import sys
import win32com.client
import argparse
import KlAkOAPI.ConnectionHelper
from KlAkOAPI.Params import KlAkParams, KlAkArray
from KlAkOAPI.Base import KlAkBase
from KlAkOAPI.Error import KlAkError
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.ChunkAccessor import KlAkChunkAccessor
from KlAkOAPI.AsyncActionStateChecker import KlAkAsyncActionStateChecker

def PrintGroupsTree(arrGroups, nLevel):
    """ Recursively prints KSC group structure. """
    for group in arrGroups:
        nId = group['id']
        strName = group['name']
        strIndention = '    '
        for i in range(nLevel):
            strIndention += '  '
        strIndention += '+-'
        print(strIndention, 'Subgroup:', strName, ', id:', nId)
        if 'groups' in group:
            subgroups = group['groups']
            PrintGroupsTree(subgroups, nLevel + 1);
        
def Sample_EnumerateGroups(hostGroup):
    """ Prints KSC group structure. """
    print('Enumerating subgroups in root group "Managed devices":')  
    
    # get id of root group ('Managed devices' group)
    nRootGroupID = hostGroup.GroupIdGroups().RetVal()
    
    # get subgroups tree, containing all grandchildren tree with no limits 
    arrSubgroups = hostGroup.GetSubgroups(nRootGroupID, 0).RetVal()
    
    # print tree of subgroups
    if arrSubgroups == None or len(arrSubgroups) == 0:
        print ('Root group is empty')
    else:
        PrintGroupsTree(KlAkArray(arrSubgroups), 0)
        
    
def Sample_FindGroups(hostGroup, server, sFilter):
    """ Searches KSC groups that require search filter """  
    print('Searching groups that require filter "'+ sFilter+ '":')     
    
    # Some samples of filter that can be used in FindGroups call are below:
    # groups named "Comput*":
    #sFilter = '(name="Comput*")'
    # groups created before 31 march 2020:
    #sFilter = '(creationDate<"2020-03-31T00:00:00Z")'
    # groups with one or more dvices with status 'Critical':
    #sFilter = '(KLGRP_CHLDHST_CNT_CRT >= 1)'
    # groups where amount of computers >= 100 (not including computers in subgroups):
    #sFilter = '(KLGRP_CHLDHST_CNT >= 100)'
    # all groups:
    #sFilter = ''
    # large groups created recently:
    #sFilter = '(&(KLGRP_CHLDHST_CNT >= 1000)(creationDate>"2020-03-31T19:00:00Z"))'
    
    res = hostGroup.FindGroups(sFilter, vecFieldsToReturn=['id', 'name', 'grp_full_name', 'parentId', 'level'], vecFieldsToOrder = [], pParams = {}, lMaxLifeTime=100)
    print('Found ' + str(res.RetVal()) + ' groups:')    
    strAccessor = res.OutPar('strAccessor')
        
    # chunkAccessor object allows iteration over search results
    chunkAccessor = KlAkChunkAccessor (server)
    items_count = chunkAccessor.GetItemsCount(strAccessor).RetVal()
    start = 0
    step = 20000
    while start < items_count:        
        res_chunk = chunkAccessor.GetItemsChunk(strAccessor, start, step)
        for group_param in KlAkArray(res_chunk.OutPar('pChunk')['KLCSP_ITERATOR_ARRAY']):
            print (group_param['grp_full_name'])
        start += step


def ProcessOU(hostGroup, nGroupID, command, strDN, nLevel):
    """" Recursively process AD organizational units and create correspondent group structure in KSC. """
    # set query string for command object
    command.CommandText = '<LDAP://' + strDN + '>;(&(objectCategory=organizationalUnit)(|(!(showInAdvancedViewOnly=*))(showInAdvancedViewOnly=0)));name, distinguishedName;oneLevel';
    rs = command.Execute()[0];

    # process returned recordset
    i = 0   # TODO: counter used for depth restriction,  in final version remove it
    while not rs.EOF:
        strNewName = rs.Fields('name').Value
        strNewDN = rs.Fields('distinguishedName').Value

        # log found OU with proper indentation
        print('  ' * nLevel, '+-', strNewName);

        # create KSC group for found OU
        nIdNewGroup = hostGroup.AddGroup({'name': str(strNewName), 'parentId': nGroupID});

        # process subOUs recursively
        if nLevel < 2:
            ProcessOU(hostGroup, nIdNewGroup.RetVal(), command, strNewDN, nLevel+1);
       
        if i > 2:
            return
        
        rs.MoveNext()
        i+=1
        
        
def Sample_Add_AD_Groups(hostGroup):    
    """ Creating group structure based on AD organization units structure """
    print('Creating group structure based on AD organization units structure')
    
    #Get Default Naming Context
    oRootDSE = win32com.client.GetObject('LDAP://RootDSE')
    strDefaultNamingContext = oRootDSE.Get('defaultNamingContext');
    print ('- DefaultNamingContext is:', strDefaultNamingContext)
    
    # prepare connection to AD
    conn = win32com.client.Dispatch('ADODB.Connection')
    conn.Provider = 'ADSDSOObject'
    conn.Open('Active Directory Provider')
    
    # prepare command object
    command = win32com.client.Dispatch('ADODB.Command');
    command.ActiveConnection = conn;
        
    # creating group where AD structure is to be duplicated
    print('- creating "process_ou" group in Managed devices group')
    rootGroupId = hostGroup.GroupIdGroups().RetVal()
    nGroupId = hostGroup.AddGroup({'name': 'process_ou', 'parentId': rootGroupId}).RetVal()
    
    # iterating AD
    print('- iterating AD structure and adding correspondent subgroups in group created above')    
    ProcessOU(hostGroup, nGroupId, command, strDefaultNamingContext, nLevel=1)
    
    # close conection
    conn.Close()
    
    print('Group structure duplicated from AD successfully')
    return nGroupId

        
def Sample_RemoveGroup(hostGroup, server, nGroupId):
    """ Removing a group """
    print('Removing group')
    
    # retrieve group name from id
    groupInfo = hostGroup.GetGroupInfo(nGroupId).RetVal()
    print('Group to remove is: ' + groupInfo['grp_full_name'])
    
    # check for root group
    if nGroupId == hostGroup.GroupIdGroups().RetVal():
       print('Cannot delete root group, please use another group id')
       return
    
    # remove group asynchronously
    res = hostGroup.RemoveGroup(nGroup = nGroupId, nFlags = 1)
    strActionGuid = res.OutPar('strActionGuid')
    
    # check for result of asynchronous action
    asyncActionStateChecker = KlAkAsyncActionStateChecker (server)
    while True:
        res = asyncActionStateChecker.CheckActionState(strActionGuid)
        if res.OutPar('bFinalized'):
            if res.OutPar('bSuccededFinalized'):
                # got asynchronous result: success 
                print ('Group deleted successfully')
            else:
                # got asynchronous result: some error occurred
                err_description = KlAkParams(res.OutPar('pStateData'))
                print('Cannot delete group:', err_description['GNRL_EA_DESCRIPTION'], '(error code ' + str(err_description['KLBLAG_ERROR_INFO']['KLBLAG_ERROR_CODE']) + ')')
            return
        else:
            # asynchronous result is not ready yet - need to wait for lNextCheckDelay milliseconds
            time.sleep(MillisecondsToSeconds(res.OutPar('lNextCheckDelay')))

        
def Sample_AddGroup(hostGroup, sGroupName, nParentGroupId):
    """ Adds KSC group """
    print('Adding subgroup ' + sGroupName + ' into "Managed devices" group')
    
    # check if group already exists
    res = hostGroup.FindGroups('(name="' + sGroupName + '")', ['id'], [], {}, 100)
    if res.RetVal() > 0:
        print ('Group ' + sGroupName + ' already exists')
        return
    
    # add new group    
    nGroupId = hostGroup.AddGroup({'name': sGroupName, 'parentId': nParentGroupId}).RetVal()  
    print('Group added successfully')
    return nGroupId
    
def main():
    """ This sample shows how you can enumerate groups in KSC server, search groups with some filter string, create groups structure based on your AD organizational units structure and delete group """
    print (main.__doc__)
    
    #argument parsing
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-e', action='store_true', help='Enumerate groups, shows current KSC group structure and group ids. Default action')
    parser.add_argument('-f', metavar='FILTER', action='store', help='Search group(s) using filter. Empty filter means all groups. Some filter samples are given in this module code, see Sample_FindGroups(...)')
    parser.add_argument('-r', metavar='GROUP_ID', type=int, action='store', help='Remove group GROUP_ID. Use Enumerate groups to see group ids')
    parser.add_argument('-ou', action='store_true', help='Creates KSC group structure based on AD organizational units structure')
    parser.add_argument('-a', metavar='GROUP_NAME', action='store', help='Adds subgroup to Managed devices group')
             
    KlAkOAPI.ConnectionHelper.AddConnectionArgs(parser)
    
    args = parser.parse_args()
        
    # enumerating group is default action
    if args.f == None and args.r == None and args.ou == False and args.a == None:
        args.e = True
    
    #connect to KSC server using basic auth by default
    server = KlAkOAPI.ConnectionHelper.ConnectFromCmdline(args)
    
    #use server object to construct objects wrapping KLOAPI calls 
    hostGroup = KlAkHostGroup(server)
    
    # call samples depending on args
    if args.e:
        Sample_EnumerateGroups(hostGroup);
    
    if not args.f == None:
        Sample_FindGroups(hostGroup, server, args.f)

    if args.ou:
        Sample_Add_AD_Groups(hostGroup)
    
    if not args.r == None:
        Sample_RemoveGroup(hostGroup, server, args.r)
        
    if args.a:
        Sample_AddGroup(hostGroup, args.a, hostGroup.GroupIdGroups().RetVal())
    
if __name__ == '__main__':
    main()