from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials



class google_calendar():

    def __init__(self):
        self.token_path = 'token.json'
        creds = Credentials.from_authorized_user_file(self.token_path)
        self.service = build("calendar", "v3", credentials=creds)
        self.calendar_id = '5e9fd551a6b862fb18072083f65f88b9c1e3c93546523d0f0ea2ebdea4937f02@group.calendar.google.com'
    def get_upcoming_events(self):
        pass

    def add_event(self, start, end, title, status):
        if status == 'Aktiv':
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
        event = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()

    def sync_dataframe(self, df):
        event_list = self.service.events().list(calendarId=self.calendar_id).execute()
        existing_events = []
        for event in event_list.get('items', []):
            start = event.get('start')
            end = event.get('end')
            summary = event.get('summary')
            if start and end and summary:
                if start.get('dateTime') and end.get('dateTime'):
                    starttime = start.get('dateTime')
                    endtime = end.get('dateTime')
                    existing_events.append((starttime, endtime, summary))
        for i, row in df.iterrows():
            if (row['starttime'], row['endtime'], row['function']) not in existing_events:
                self.add_event(row['starttime'], row['endtime'], row['function'], row['status'])
                                         
                                #self.add_event(row['starttime'], row['endtime'], row['function'], row['status'])
    
    def delete_event(self, event_id):
        try:
            self.service.events().delete(self.calendar_id, event_id)
        
        except HttpError as err:
            raise err._get_reason()  

    