from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime
import logging
import os


SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
    creds = None
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, 'token.json')
    creds_path = os.path.join(script_dir, 'credentials.json')

    # Load existing credentials
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next time
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service



def reformat_wellhub_events(service, calendar_id='primary'):
    # Get upcoming events (adjust time range as needed)
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=100,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    for event in events:
        summary = event.get('summary', '')
        if summary.startswith('Wellhub'):
            parts = summary.split(' - ', 2)  # Split into at most 3 parts
            if not len(parts) == 3:
                logging.warning(f"Skipping: {summary} (unexpected format), {parts}")
            else:
                wellhub, location, title = parts
                new_summary = f"{title} - {location} - {wellhub}"
                print(f"Updating: {summary} → {new_summary}")
                event['summary'] = new_summary
                service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()


service = get_calendar_service()
reformat_wellhub_events(service)

# keep the console open for debugging
# input("Press Enter to exit...")