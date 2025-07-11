import frappe
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from edu_quality.api.google_service_auth import get_absolute_path


def get_google_service_object():
    """Returns google service object"""
    google_settings = frappe.get_single("Google Service Account")
    credentials = service_account.Credentials.from_service_account_file(
        get_absolute_path(google_settings.service_account_credentials_json),
        scopes=['https://www.googleapis.com/auth/calendar.readonly'],
    )

    return build(
        serviceName='calendar',
        version='v3',
        credentials=credentials,
    )


@frappe.whitelist(allow_guest=True)
def get_calender_events(school):
    try:
        calendar_id = frappe.get_value("School", school, "calendar_id")
        # Get events from the primary calendar
        now = datetime.now()
        year_start = datetime(now.year, 4, 1).isoformat() + 'Z'
        year_end = datetime(now.year + 1, 3, 31).isoformat() + 'Z'   
        # Get events within the current month
        service = get_google_service_object()
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=year_start,
            timeMax=year_end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        event_list = []

        if not events:
            return 'No upcoming events found.'
        else:
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                event_list.append({"start": start, "end": end, "event": event['summary']})

        return event_list
    except:
        frappe.log_error('Bonafide Certificate Sending Failed', frappe.get_traceback())
        frappe.response['message'] = "Error occurred while fetching calendar events"