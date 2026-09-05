import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from datetime import datetime, timedelta, timezone

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# ============================================================================
# CONFIGURATION
# ============================================================================
# How many days ahead to keep the calendar synced. Softadmin itself decides
# how many shifts it actually shows/allows booking for; this only bounds how
# far ahead we look at existing calendar events for cleanup/dedup purposes.
CALENDAR_SYNC_DAYS = int(os.environ.get("CALENDAR_SYNC_DAYS", "75"))


class google_calendar():
    def __init__(self):
        self.token_path = 'token.json'
        creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # Refresh expired token so the script never fails due to a stale access token
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as err:
                raise Exception(
                    "Google OAuth refresh token is invalid, expired, or has been revoked "
                    "(original error: {}). You need to regenerate token.json locally "
                    "(re-run the OAuth flow / quickstart.py) and update the GOOGLE_TOKEN "
                    "GitHub secret with the new token contents.".format(err)
                )

        self.service = build("calendar", "v3", credentials=creds)
        # Always defaults to the dedicated Parpas Shifts calendar.
        # Override only via the CALENDAR_ID secret/env var if you deliberately
        # want to point elsewhere -- never default to 'primary'.
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
        try:
            self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
        except HttpError as err:
            raise Exception(
                "Failed to insert event '{}' ({} -> {}) into calendar {}: {}".format(
                    title, start, end, self.calendar_id, err
                )
            )

    def _get_all_events(self):
        """Fetch events from the calendar within the sync window, handling pagination."""
        existing_events = []
        event_ids = {}
        page_token = None

        time_min = datetime.now(timezone.utc).isoformat()
        time_max = (datetime.now(timezone.utc) + timedelta(days=CALENDAR_SYNC_DAYS)).isoformat()

        while True:
            try:
                response = self.service.events().list(
                    calendarId=self.calendar_id,
                    pageToken=page_token,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    maxResults=2500,
                ).execute()
            except HttpError as err:
                raise Exception(
                    "Failed to list events from calendar {}: {}".format(self.calendar_id, err)
                )

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
        added, deleted = 0, 0

        for i, row in df.iterrows():
            # Only sync shifts marked 'Aktiv' on PARPAS
            if row['status'] == 'Aktiv':
                shift_key = (row['starttime'], row['endtime'], row['function'])
                df_shifts.append(shift_key)
                if shift_key not in existing_events:
                    print("Event added\n", "Starttime:", row['starttime'], "Endtime:", row['endtime'], "Function:", row['function'])
                    self.add_event(row['starttime'], row['endtime'], row['function'], row['status'])
                    added += 1

        # Remove events that were previously synced but are no longer active on PARPAS
        # (shift swapped, approved leave, etc.) within the sync window.
        for event_set in existing_events:
            if event_set not in df_shifts:
                print("Event deleted\n", "Starttime:", event_set[0], "Endtime:", event_set[1], "Function:", event_set[2])
                self.delete_event(event_ids.get(event_set))
                deleted += 1

        print("Sync summary: {} added, {} deleted, {} unchanged".format(
            added, deleted, len(existing_events) - deleted
        ))
        return {"added": added, "deleted": deleted}

    def delete_event(self, event_id):
        if not event_id:
            return
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
        except HttpError as err:
            # 410 Gone means it's already deleted -- not a real failure, don't crash the run
            if err.resp.status == 410:
                print("Event {} already deleted, skipping.".format(event_id))
                return
            raise Exception("Failed to delete event {}: {}".format(event_id, err))
