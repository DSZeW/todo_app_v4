from __future__ import print_function
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Port par défaut modifié ici (5000)
SCOPES = ['https://www.googleapis.com/auth/calendar']

def add_event_to_google_calendar(title, start_datetime_str):
    """
    Ajoute un événement à Google Agenda.
    :param title: Titre de la tâche (ex: "Faire les courses")
    :param start_datetime_str: Date et heure de début en format 'YYYY-MM-DDTHH:MM:SS'
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Ici on installe le flow avec redirection sur le bon port (5000)
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=5000)  # 👈 placement correct ici
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Date/heure de début et fin (+1h par défaut)
    start = start_datetime_str
    end = (datetime.datetime.fromisoformat(start_datetime_str) + datetime.timedelta(hours=1)).isoformat()

    event = {
        'summary': title,
        'start': {
            'dateTime': start,
            'timeZone': 'Europe/Paris',
        },
        'end': {
            'dateTime': end,
            'timeZone': 'Europe/Paris',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"\u2705 Événement créé : {event.get('htmlLink')}")
