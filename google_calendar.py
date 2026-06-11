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

    def sync_dataframe(self, df):
        event_list = self.service.events().list(calendarId=self.calendar_id).execute()
        existing_events = []
        event_ids = {}
        df_shifts = []

        for event in event_list.get('items', []):
            start = event.get('start')
            end = event.get('end')
            summary = event.get('summary')
            if start and end and summary:
                if start.get('dateTime') and end.get('dateTime'):
                    starttime = start.get('dateTime')
                    endtime = end.get('dateTime')
                    
                    # Skapa lista och dictionary av alla pass som finns i kalendern redan.
                    existing_events.append((starttime, endtime, summary))

                    event_ids[(starttime, endtime, summary)] = event.get('id')

        for i, row in df.iterrows():
        
            # Skapa lista på alla pass som är 'Aktiva' på PARPAS
            if row['status'] == 'Aktiv':
                df_shifts.append((row['starttime'], row['endtime'], row['function']))

                # Om passet på PARPAS inte redan finns i kalendern, lägg till.
                if (row['starttime'], row['endtime'], row['function']) not in existing_events:
                    print("Event added\n", "Starttime:", event_set[0], "Endtime:", event_set[1], "Function:", event_set[2])

                    self.add_event(row['starttime'], row['endtime'], row['function'], row['status'])
                                         
        # Om passet finns i kalendern men har tagits bort från PARPAS (Bytt pass eller beviljad ledighet etc.), ta bort.
        for event_set in existing_events:
            if event_set not in df_shifts:
                print("Event deleted\n", "Starttime:", event_set[0], "Endtime:", event_set[1], "Function:", event_set[2])
                self.delete_event(event_ids.get(event_set))

    def delete_event(self, event_id):
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
        
        except HttpError as err:
            raise err._get_reason()  

    