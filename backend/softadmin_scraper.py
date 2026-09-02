"""
Softadmin Shift Scraper - Extended Booking Window Version
Scrapes available shifts from Softadmin system with 2+ month advance booking
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION - EXTENDED BOOKING WINDOW
# ============================================================================
# Changed from default ~21-30 days to 75 days (2.5 months advance booking)
BOOKING_WINDOW_DAYS = int(os.getenv('BOOKING_WINDOW_DAYS', '75'))
BOOKING_BUFFER_DAYS = int(os.getenv('BOOKING_BUFFER_DAYS', '3'))

# Softadmin credentials
SOFTADMIN_USERNAME = os.getenv('SOFTADMIN_USERNAME')
SOFTADMIN_PASSWORD = os.getenv('SOFTADMIN_PASSWORD')
SOFTADMIN_BASE_URL = os.getenv('SOFTADMIN_BASE_URL', 'https://grona.softadmin.se')

# Session configuration
SESSION_TIMEOUT = 30
MAX_RETRIES = 3

class SoftadminScraper:
    """Scraper for Softadmin shift booking system with extended date range"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = SOFTADMIN_BASE_URL
        self.is_authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate with Softadmin system"""
        login_url = f"{self.base_url}/Account/LogOn"
        
        payload = {
            'Username': SOFTADMIN_USERNAME,
            'Password': SOFTADMIN_PASSWORD,
            'ReturnUrl': '/'
        }
        
        try:
            response = self.session.post(
                login_url,
                data=payload,
                timeout=SESSION_TIMEOUT,
                allow_redirects=True
            )
            
            if response.status_code == 200 and 'LogOff' in response.text:
                self.is_authenticated = True
                print(f"✓ Authenticated successfully")
                return True
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False
    
    def get_date_range(self) -> tuple:
        """
        Calculate the date range for shift scraping.
        EXTENDED: Now books 2+ months (75 days) in advance instead of ~3-4 weeks
        """
        today = datetime.now()
        start_date = today
        end_date = today + timedelta(days=BOOKING_WINDOW_DAYS)
        
        print(f"📅 Booking window: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({BOOKING_WINDOW_DAYS} days)")
        return start_date, end_date
    
    def fetch_shifts(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch available shifts within the booking window.
        Uses extended date range by default.
        """
        if not self.is_authenticated:
            if not self.authenticate():
                return []
        
        if start_date is None or end_date is None:
            start_date, end_date = self.get_date_range()
        
        shifts = []
        
        try:
            shifts_url = f"{self.base_url}/Shift/Available"
            params = {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'page': 1
            }
            
            print(f"🔍 Fetching shifts from {params['from']} to {params['to']}")
            
            response = self.session.get(
                shifts_url,
                params=params,
                timeout=SESSION_TIMEOUT
            )
            
            if response.status_code == 200:
                shifts = self._parse_shifts(response.text)
                print(f"✓ Found {len(shifts)} shifts")
            else:
                print(f"✗ Failed to fetch shifts: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error fetching shifts: {e}")
        
        return shifts
    
    def _parse_shifts(self, html: str) -> List[Dict]:
        """Parse shift data from HTML response"""
        shifts = []
        soup = BeautifulSoup(html, 'html.parser')
        
        shift_elements = soup.select('.shift-card, .shift-item, tr.shift-row')
        
        for element in shift_elements:
            try:
                shift_data = {
                    'id': element.get('data-shift-id', ''),
                    'date': element.get('data-date', ''),
                    'start_time': element.get('data-start', ''),
                    'end_time': element.get('data-end', ''),
                    'role': element.get('data-role', ''),
                    'location': element.get('data-location', ''),
                    'available_spots': element.get('data-spots', '0'),
                }
                shifts.append(shift_data)
            except Exception as e:
                continue
        
        return shifts
    
    def book_shift(self, shift_id: str) -> bool:
        """Book a specific shift"""
        if not self.is_authenticated:
            if not self.authenticate():
                return False
        
        try:
            book_url = f"{self.base_url}/Shift/Book/{shift_id}"
            response = self.session.post(
                book_url,
                timeout=SESSION_TIMEOUT,
                headers={'X-Requested-With': 'XMLHttpRequest'}
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Shift {shift_id} booked successfully")
                return True
            else:
                print(f"✗ Failed to book shift {shift_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error booking shift: {e}")
            return False
    
    def close(self):
        """Close the session"""
        self.session.close()


def main():
    """Main function to demonstrate extended booking window"""
    print("=" * 60)
    print("AUTOSHIFT - Extended Booking Window (2+ Months)")
    print("=" * 60)
    
    scraper = SoftadminScraper()
    
    try:
        if not scraper.authenticate():
            print("Failed to authenticate. Check credentials.")
            return
        
        start_date, end_date = scraper.get_date_range()
        shifts = scraper.fetch_shifts(start_date, end_date)
        
        print(f"\n📊 Summary:")
        print(f"   Total shifts found: {len(shifts)}")
        print(f"   Booking window: {BOOKING_WINDOW_DAYS} days")
        print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
