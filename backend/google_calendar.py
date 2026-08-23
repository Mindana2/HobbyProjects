import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class google_calendar():

    def __init__(self):
        self.token_path = 'token.json'
        creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # Refresh expired token so the script never fails due to a stale access token
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        self.service = build("calendar", "v3", credentials=creds)
        self.calendar_id = os.environ.get(
            'CALENDAR_ID',
            '9be1390db5471287b61e4bce2393af92c5d2434edab90db3aa96b20554437bf2@group.calendar.google.com'
        )

    def get_upcoming_events(self):
        pass

    def add_event(self, start, end, title, status):
        event = {
            'summary': title,
            'start': {
                'dateTime': start,
                'timeZone': 'Europe/Stockholm'
            },
            'end': {
                'dateTime': end,
                'timeZone': 'Europe/Stockholm'
            }
        }
        self.service.events().insert(calendarId=self.calendar_id, body=event).execute()

    def _get_all_events(self):
        """Fetch ALL events from the calendar, handling pagination."""
        existing_events = []
        event_ids = {}
        page_token = None

        while True:
            response = self.service.events().list(
                calendarId=self.calendar_id,
                pageToken=page_token,
                maxResults=2500,
            ).execute()

            for event in response.get('items', []):
                start = event.get('start')
                end = event.get('end')
                summary = event.get('summary')
                if start and end and summary:
                    if start.get('dateTime') and end.get('dateTime'):
                        starttime = start.get('dateTime')
                        endtime = end.get('dateTime')
                        existing_events.append((starttime, endtime, summary))
                        event_ids[(starttime, endtime, summary)] = event.get('id')

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return existing_events, event_ids

    def sync_dataframe(self, df):
        existing_events, event_ids = self._get_all_events()
        df_shifts = []

        for i, row in df.iterrows():
            # Skapa lista pa alla pass som ar 'Aktiva' pa PARPAS
            if row['status'] == 'Aktiv':
                df_shifts.append((row['starttime'], row['endtime'], row['function']))

                # Om passet pa PARPAS inte redan finns i kalendern, lagg till.
                if (row['starttime'], row['endtime'], row['function']) not in existing_events:
                    print("Event added\n", "Starttime:", row['starttime'], "Endtime:", row['endtime'], "Function:", row['function'])
                    self.add_event(row['starttime'], row['endtime'], row['function'], row['status'])

        # Om passet finns i kalendern men har tagits bort fran PARPAS, ta bort.
        for event_set in existing_events:
            if event_set not in df_shifts:
                print("Event deleted\n", "Starttime:", event_set[0], "Endtime:", event_set[1], "Function:", event_set[2])
                self.delete_event(event_ids.get(event_set))

    def delete_event(self, event_id):
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
        except HttpError as err:
            raise Exception(err._get_reason())
