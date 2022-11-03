from __future__ import print_function
from driveapi import getParentID

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/admin.reports.audit.readonly']

def main():
    """Shows basic usage of the Admin SDK Reports API.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('admin', 'reports_v1', credentials=creds)

    # Call the Admin SDK Reports API
    results = service.activities().list(userKey='all', applicationName='drive').execute()
    activities = results.get('items', [])

    if not activities:
        print('No activities found.')
    else:
        print('Activity Logs:')
        for activity in activities:
            activityTime = activity['id']['time']
            eventDetails = activity['events'][0]
            actorID = list(activity['actor'].values())
            eventName = eventDetails['name']
            if(activity['events'][0]['name'] == 'change_user_access'):
                eventName = 'PermissionChange'


            # Extract Activity Parameters
            parameterList = eventDetails['parameters']

            # For create action
            if(eventName == 'create'):
                doc_id = parameterList[2]['value']
                logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(actorID[1])

            # For delete or trash action
            elif(eventName == 'delete' or eventName == 'trash'):
                doc_id = parameterList[2]['value']
                logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(actorID[1])

            # For edit action changes
            elif(eventName == 'edit'):
                doc_id = parameterList[2]['value']
                # Change User Access (PermissionChange) and Rename actions are logged
                if(len(activity['events']) != 1):
                    # Permission Change event
                    if(activity['events'][1]['type'] == 'acl_change'):
                        permissionChange = activity['events'][1]['parameters']
                        target_user = permissionChange[3]['value']
                        eventName = 'PermissionChange'
                        old_permissions = permissionChange[4]['multiValue']
                        new_permissions = permissionChange[5]['multiValue']
                        old_permission = ""
                        new_permission = ""

                        for item in old_permissions:
                            old_permission = old_permission + item

                        for item in new_permissions:
                            new_permission = new_permission + item

                        eventName = eventName + "-to:" + new_permission + "-from:" + old_permission + "-for:" + target_user
                    else:
                        eventName = 'rename'

                logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(actorID[1])

            # For Access permission change action
            elif(eventName == 'PermissionChange'):

                doc_id = parameterList[7]['value']

                target_user = parameterList[3]['value']
                old_permissions = parameterList[4]['multiValue']
                new_permissions = parameterList[5]['multiValue']
                old_permission = ""
                new_permission = ""

                for item in old_permissions:
                    old_permission = old_permission + item

                for item in new_permissions:
                    new_permission = new_permission + item

                eventName = eventName + "-to:" + new_permission + "-from:" + old_permission + "-for:" + target_user
                logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(actorID[1])

            # For move action
            elif(eventName == 'move'):
                
                doc_id = parameterList[6]['value']
                srcFolderID = parameterList[3]['multiValue'][0]
                dstFolderID = parameterList[5]['multiValue'][0]

                eventName = eventName + ":" + str(srcFolderID) + ":" + str(dstFolderID)
                logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(actorID[1])
            else:
                continue

            # Get Parent ID from the Drive API
            parentID = getParentID(doc_id)
            if(parentID == None):
                parentID = "None"
            logActivity = logActivity + "\t*\t" + parentID
            print(logActivity)

if __name__ == '__main__':
    main()