# #!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""This module presents samples of usage KlAkOAPI package to create task"""

import socket
import time
from sys import platform
from KlAkOAPI.Params import KlAkParams, KlAkArray
from KlAkOAPI.AdmServer import KlAkAdmServer
from KlAkOAPI.Tasks import KlAkTasks
from KlAkOAPI.HostGroup import KlAkHostGroup
from KlAkOAPI.EventProcessing import KlAkEventProcessing

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
    
def CreateTask(oTasks, nGroupId):
    """ Creates group task named 'kloapiTask', task type is nagent's 'show message', Manual schedule, task's group is Managed devices group (group id = 0) """
    
    # compose params that keeps settings of notification about changing task state
    pNotifDefault = KlAkParams({'KLEVP_ND_DAYS_TO_STORE_EVENT': 1, 'KLEVP_ND_EVETN_TYPE': 'KLPRCI_TaskState', 'KLEVP_ND_STORE_AT_CLIENT_LOG': False, 'KLEVP_ND_STORE_AT_CLIENT_PRES': False, 'KLEVP_ND_STORE_AT_SERVER_LOG': False})
    pInfNotif_TaskRunning = KlAkParams(pNotifDefault)
    pInfNotif_TaskRunning.AddParams('KLEVP_ND_BODY_FILTER', {'KLPRCI_newState': 1})
    pInfNotif_TaskSuspended = KlAkParams(pNotifDefault)
    pInfNotif_TaskSuspended.AddParams('KLEVP_ND_BODY_FILTER', {'KLPRCI_newState': 2})
    pInfNotif_TaskCompleted = KlAkParams(pNotifDefault)
    pInfNotif_TaskCompleted.AddParams('KLEVP_ND_BODY_FILTER', {'KLPRCI_newState': 4})
    pInfNotif = KlAkParams(pNotifDefault)
    pInfNotif.AddString('KLEVP_ND_EVETN_TYPE', 'KLEVP_GroupTaskSyncState')
    pNotif = KlAkParams({'ERR': [pNotifDefault], 'INF': [pInfNotif, pInfNotif_TaskRunning, pInfNotif_TaskSuspended, pInfNotif_TaskCompleted], 'WRN': [pNotifDefault] })
    
    # compose params that contains info about task to be created: task type 'show message', schedule type 'start manually', display name 'kloapiTask', acts in group 'Managed devices', notify about state changes
    oTaskParams = KlAkParams({'TASKID_COMPONENT_NAME': '86', 'TASKID_PRODUCT_NAME': '1103', 'TASKID_VERSION': '1.0.0.0', 'TASK_NAME': 'KLNAG_TASK_SHOW_MSG'})
    oTaskParams.AddParams('TASK_ADDITIONAL_PARAMS', {'KLNAG_MSG_TEXT': 'Test message'})
    oTaskParams.AddInt('TASKSCH_TYPE', 0)
    oTaskParams.AddParams('TASK_INFO_PARAMS', {'DisplayName': 'kloapiTask', 'PRTS_TASK_GROUPID': nGroupId, 'klprts-TaskScheduleSubtype': 256, 'KLPRSS_EVPNotifications': pNotif})
    
    # create task
    strTaskId = oTasks.AddTask(oTaskParams).RetVal()
    print('Created task id is:', strTaskId)
    return strTaskId

def GetLastTaskResult(server, oTasks, strID):
    """ Prints task history and returns last state """
    #fill object with required fields
    oFields2Return = KlAkArray(['event_type', 'task_new_state', 'event_id', 'rise_time'])

    #sort descending by publication time
    oSortFields = KlAkArray([{'Name': 'rise_time', 'Asc' : False}])

    #we need only task state events
    oFilter = KlAkParams({'event_type': 'KLPRCI_TaskState'})

    oHistory = oTasks.GetTaskHistory(strID, oFields2Return, oSortFields, '', oFilter)

    oResult = None
    strIteratorId = oHistory.OutPar('strIteratorId')
    eventProcessing = KlAkEventProcessing(server)
    if eventProcessing.GetRecordCount(strIteratorId).RetVal() > 0:
        pParamsEvents = eventProcessing.GetRecordRange( strIteratorId, 0, eventProcessing.GetRecordCount(strIteratorId).RetVal() )

        for item in pParamsEvents.OutPar('pParamsEvents')['KLEVP_EVENT_RANGE_ARRAY']:
            print('--- event --')
            print( 'event_id: ', item['event_id'],  '\tevent_type: ', item['event_type'], '\ttask_new_state: ', item['task_new_state'], '\trise_time: ', item['rise_time'])

            nState = item['task_new_state']
            if 3 == nState or 4 == nState : # if failed or completed successfully
                oResult = item
                break
                
        eventProcessing.ReleaseIterator(strIteratorId)

    return oResult

def RunTaskAndReturnResult(server, oTasks, strID):
    """ Runs task and checks for result """
    oInfo = oTasks.GetTask(strID).RetVal()
    print('Processing task ' + oInfo['DisplayName'] + ' created at ' + oInfo['PRTS_TASK_CREATION_DATE'].isoformat() )

    # print task statistics into the log
    oStatistics = oTasks.GetTaskStatistics(strID).RetVal()

    print('Task statistics' )
    print('Not distributed: ', oStatistics['1'])
    print('Running: ', oStatistics['2'])
    print('OK: ', oStatistics['4'])
    print('Warning: ', oStatistics['8'])
    print('Failed: ', oStatistics['16'])
    print('Scheduled: ', oStatistics['32'])
    print('Paused: ', oStatistics['64'])

    #initial task state (before task start)
    oState0 = GetLastTaskResult(server, oTasks, strID)

    oTasks.RunTask( strID )

    # wait for a 5 seconds
    time.sleep(5)

    nResult = None
    while True:
        oState1 = GetLastTaskResult(server, oTasks, strID)
        if  ( None == oState0 and None != oState1) or ( None != oState1 and  None != oState0 and  oState1['event_id'] != oState0['event_id']):
            print('Task result is ', oState1['task_new_state'])
            nResult = oState1['task_new_state']
            break
        time.sleep(5)

    # return final task state (before task start)
    return nResult
    
    
def main():
    """ This sample shows how you can create a task """
    print (main.__doc__)

    #connect to KSC server using basic auth by default
    server = GetServer()

    oHostGroup = KlAkHostGroup(server)
    nRootGroupId = oHostGroup.GroupIdGroups().RetVal()
    
    oTasks = KlAkTasks(server)
    strCreatedTask = CreateTask(oTasks, nRootGroupId)
    nResult = RunTaskAndReturnResult(server, oTasks, strCreatedTask)
    if 4 == nResult:
        print('Task result is Success')
    else:
        print('Task result is Failure')


    
if __name__ == '__main__':
    main()