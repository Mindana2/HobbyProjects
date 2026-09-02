"""
Google Calendar Integration - Extended Booking Window
Syncs shifts from Softadmin to Google Calendar with 2+ month advance booking
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION - EXTENDED BOOKING WINDOW
# ============================================================================
CALENDAR_SYNC_DAYS = int(os.getenv('CALENDAR_SYNC_DAYS', '75'))
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')

class GoogleCalendarSync:
    """Sync shifts to Google Calendar with extended date range"""
    
    def __init__(self):
        self.service = None
        self.calendar_id = CALENDAR_ID
        
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle
        
        creds = None
        
        if os.path.exists(GOOGLE_TOKEN_FILE):
            with open(GOOGLE_TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_CREDENTIALS_FILE,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                creds = flow.run_local_server(port=0)
            
            with open(GOOGLE_TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        print("✓ Google Calendar authenticated")
        return True
    
    def get_date_range(self) -> tuple:
        """
        Calculate calendar sync date range.
        EXTENDED: Syncs 2+ months (75 days) in advance
        """
        today = datetime.now()
        start_date = today
        end_date = today + timedelta(days=CALENDAR_SYNC_DAYS)
        
        print(f"📅 Calendar sync: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({CALENDAR_SYNC_DAYS} days)")
        return start_date, end_date
    
    def create_shift_event(self, shift: Dict) -> Optional[str]:
        """Create a calendar event for a shift"""
        if not self.service:
            self.authenticate()
        
        try:
            shift_date = shift.get('date', '')
            start_time = shift.get('start_time', '09:00')
            end_time = shift.get('end_time', '17:00')
            
            event_start = f"{shift_date}T{start_time}:00"
            event_end = f"{shift_date}T{end_time}:00"
            
            event = {
                'summary': f"Shift - {shift.get('role', 'Worker')}",
                'description': f"Location: {shift.get('location', 'TBD')}\nShift ID: {shift.get('id', '')}",
                'start': {
                    'dateTime': event_start,
                    'timeZone': 'Europe/Stockholm',
                },
                'end': {
                    'dateTime': event_end,
                    'timeZone': 'Europe/Stockholm',
                },
                'colorId': '9',
            }
            
            event_result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            event_id = event_result.get('id')
            print(f"✓ Calendar event created: {event_id}")
            return event_id
            
        except Exception as e:
            print(f"✗ Error creating calendar event: {e}")
            return None
    
    def sync_shifts(self, shifts: List[Dict]) -> int:
        """Sync multiple shifts to calendar"""
        if not shifts:
            return 0
        
        created_count = 0
        
        for shift in shifts:
            event_id = self.create_shift_event(shift)
            if event_id:
                created_count += 1
        
        print(f"✓ Synced {created_count}/{len(shifts)} shifts to calendar")
        return created_count
    
    def list_upcoming_events(self, max_results: int = 10) -> List[Dict]:
        """List upcoming calendar events"""
        if not self.service:
            self.authenticate()
        
        try:
            now = datetime.now().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except Exception as e:
            print(f"✗ Error listing events: {e}")
            return []


def main():
    """Demo calendar sync with extended window"""
    print("=" * 60)
    print("GOOGLE CALENDAR SYNC - Extended Window (2+ Months)")
    print("=" * 60)
    
    sync = GoogleCalendarSync()
    
    try:
        sync.authenticate()
        start_date, end_date = sync.get_date_range()
        
        print(f"\n📊 Calendar sync configured for {CALENDAR_SYNC_DAYS} days")
        print(f"   Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
