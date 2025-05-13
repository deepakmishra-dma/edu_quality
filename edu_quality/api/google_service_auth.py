import json
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from requests import get, post
import frappe
from urllib.parse import quote
from apiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
import frappe.integrations.google_oauth as oauth


CALLBACK_METHOD = "/api/method/frappe.integrations.google_oauth.callback"
_SCOPES = {
    "admin": ["https://www.googleapis.com/auth/admin.directory.user","https://www.googleapis.com/auth/admin.directory.group","https://www.googleapis.com/auth/admin.directory.group.member"],
    "mail": ("https://mail.google.com/"),
    "contacts": ("https://www.googleapis.com/auth/contacts"),
    "drive": ("https://www.googleapis.com/auth/drive"),
    "indexing": ("https://www.googleapis.com/auth/indexing"),
    "calendar":   ['https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/calendar.events']
    }
_SERVICES = {
    "admin": ("admin", "directory_v1"),
    "contacts": ("people", "v1"),
    "drive": ("drive", "v3"),
    "indexing": ("indexing", "v3"),
    "calendar": ("calendar", "v3"),
}
_DOMAIN_CALLBACK_METHODS = {
    "mail": "frappe.email.oauth.authorize_google_access",
    "contacts": "frappe.integrations.doctype.google_contacts.google_contacts.authorize_access",
    "drive": "edu_quality.edu_quality.doctype.google_drive_settings.google_drive_settings.authorize_access",
    "indexing": "frappe.website.doctype.website_settings.google_indexing.authorize_access",
}


class GoogleServiceAccountAuth:
    def __init__(self, domain: str, validate: bool = True):
        self.google_settings = frappe.get_single("Google Service Account")

        self.domain = domain.lower()
        self.scopes = (
            " ".join(_SCOPES[self.domain])
            if isinstance(_SCOPES[self.domain], (list, tuple))
            else _SCOPES[self.domain]
        )

        if validate:
            self.validate_google_settings()

    def validate_google_settings(self):
        google_settings = "<a href='/app/google-settings'>Google Settings</a>"

        if not self.google_settings.service_account_credentials_json:
            frappe.throw(
                frappe._("Please enable {} before continuing.").format(google_settings)
            )

    def get_google_service_object(self,imporsonate_user = None,imporsonate=False):
        """Returns google service object"""
        imporsonate_usr='teacher@walnutedu.in'
        if imporsonate_user:
            imporsonate_usr = imporsonate_user
        if imporsonate:
            credentials = service_account.Credentials.from_service_account_file(
                get_absolute_path(self.google_settings.service_account_credentials_json),
                scopes={self.scopes},
                subject=imporsonate_usr
            )
        else:
            credentials = service_account.Credentials.from_service_account_file(
                get_absolute_path(self.google_settings.service_account_credentials_json),
                scopes={self.scopes}
            )    

        return build(
            serviceName=_SERVICES[self.domain][0],
            version=_SERVICES[self.domain][1],
            credentials=credentials,
            static_discovery=False,
        )
        
    def create_meet(self, summary,description, start_time, duration_minutes, imporsonate_user):
        """
        Creates a Google Meet event and returns its URL.
        
        Args:
        - summary: A string, the title of the meeting.
        - start_time: A datetime object, the start time of the meeting.
        - duration_minutes: An integer, the duration of the meeting in minutes.
        - attendees_emails: A list of strings, email addresses of attendees.
        
        Returns:
        - meet_url: A string, the URL of the created Google Meet.
        """
        service = self.get_google_service_object(imporsonate_user=imporsonate_user,imporsonate=True)
        reminders = [
            {"method": "popup", "minutes": 5},    # 5 minutes before the event
            {"method": "popup", "minutes": 20},   # 20 minutes before the event
            {"method": "email", "minutes": 60 * 12}  # 12 hours before the event (converted to minutes)
         ]
        attendess = [{'email': imporsonate_user}]
        print(attendess)
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'IST',  # Modify according to your timezone
            },
            'end': {
                'dateTime': (start_time + timedelta(minutes=duration_minutes)).strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'IST',  # Modify according to your timezone
            },
            'attendees':attendess ,
            'conferenceData': {
                'createRequest': {'requestId': 'meet'}
            },
            'reminders': {
            'overrides': reminders,
            'useDefault': False  # Set to False to use custom reminders
             }
        }
        
        event = service.events().insert(calendarId="primary", body=event, sendNotifications=True, conferenceDataVersion=1).execute()
        
        meet_url = event.get('hangoutLink')
        if meet_url:
            return meet_url
        else:
            raise Exception("Failed to create Google Meet.")

    def list_recordings(self):
        """
        Lists all Google Meet recordings.
        
        Returns:
        - recordings: A list of recording objects.
        """
        service = self.get_google_service_object()
        
        recordings = service.drive().files().list(q="mimeType='application/vnd.google-apps.folder' and name='Meet Recordings'").execute()
        recording_folder_id = recordings.get('files')[0].get('id')
        
        recordings = service.drive().files().list(q=f"'{recording_folder_id}' in parents and trashed=false").execute().get('files', [])
        
        return recordings

    def get_participants(self, recording_id):
        """
        Gets the participants list of a Google Meet recording.
        
        Args:
        - recording_id: A string, the ID of the recording.
        
        Returns:
        - participants: A list of participant objects.
        """
        service = self.get_google_service_object()
        
        participants = service.drive().files().list(q=f"'{recording_id}' in parents and trashed=false").execute().get('files', [])
        
        return participants    
    
    def get_meeting_details(self, event_id):
        """
        Retrieves details of a Google Meet event.

        Args:
        - event_id: A string, the ID of the Google Meet event.

        Returns:
        - meeting_details: A dictionary containing details of the Google Meet event, including participants and recording details.
        """
        service = self.get_google_service_object()

        # Retrieve details of the Google Meet event
        event = service.events().get(calendarId="primary", eventId=event_id).execute()

        # Get participants list
        participants = event.get('attendees', [])

        # Check if recording is available
        recording_link = None
        recording_info = service.events().instances(calendarId="primary", eventId=event_id).execute().get('items', [])
        print(recording_info)
        if recording_info:
            recording_link = recording_info[0].get('hangoutLink')

        meeting_details = {
            'participants': participants,
            'recording_link': recording_link
        }

        return meeting_details



def get_absolute_path(file_url):
    site_path = frappe.get_site_path()
    if "private" in file_url:
        file_path = site_path + file_url
    else:
        file_path = site_path + "/public" + file_url
    return file_path
