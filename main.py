"""
AutoShift - Main Entry Point
Automated shift booking with 2+ month advance booking window
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION - EXTENDED BOOKING WINDOW
# ============================================================================
BOOKING_WINDOW_DAYS = int(os.getenv('BOOKING_WINDOW_DAYS', '75'))
BOOKING_BUFFER_DAYS = int(os.getenv('BOOKING_BUFFER_DAYS', '3'))
AUTO_BOOK_ENABLED = os.getenv('AUTO_BOOK_ENABLED', 'true').lower() == 'true'
BOOK_SPECIFIC_ROLES = os.getenv('BOOK_SPECIFIC_ROLES', '').split(',') if os.getenv('BOOK_SPECIFIC_ROLES') else []
MAX_SHIFTS_PER_WEEK = int(os.getenv('MAX_SHIFTS_PER_WEEK', '5'))
SYNC_TO_CALENDAR = os.getenv('SYNC_TO_CALENDAR', 'true').lower() == 'true'

print("=" * 70)
print("AUTOSHIFT - Extended Booking System")
print("=" * 70)
print(f"✓ Booking window: {BOOKING_WINDOW_DAYS} days (extended from default ~21-30 days)")
print(f"✓ Calendar sync: {'Enabled' if SYNC_TO_CALENDAR else 'Disabled'}")
print(f"✓ Auto-booking: {'Enabled' if AUTO_BOOK_ENABLED else 'Disabled'}")
print("=" * 70)


def calculate_booking_window():
    """
    Calculate the extended booking window dates.
    
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    today = datetime.now()
    start_date = today + timedelta(days=BOOKING_BUFFER_DAYS)
    end_date = today + timedelta(days=BOOKING_WINDOW_DAYS)
    
    print(f"\n📅 Booking Window:")
    print(f"   Start: {start_date.strftime('%Y-%m-%d')} (in {BOOKING_BUFFER_DAYS} days)")
    print(f"   End:   {end_date.strftime('%Y-%m-%d')} (in {BOOKING_WINDOW_DAYS} days)")
    print(f"   Total: {BOOKING_WINDOW_DAYS - BOOKING_BUFFER_DAYS} days of shifts")
    
    return start_date, end_date


def main():
    """Main execution function"""
    print("\n🚀 Starting AutoShift with extended booking window...\n")
    
    start_date, end_date = calculate_booking_window()
    
    try:
        from backend.softadmin_scraper import SoftadminScraper
        
        scraper = SoftadminScraper()
        
        if not scraper.authenticate():
            print("✗ Failed to authenticate with Softadmin")
            return
        
        print(f"\n🔍 Fetching shifts...")
        shifts = scraper.fetch_shifts(start_date, end_date)
        
        if not shifts:
            print("No shifts found in the extended booking window")
            return
        
        print(f"✓ Found {len(shifts)} available shifts")
        
        if BOOK_SPECIFIC_ROLES:
            print(f"\n🎯 Filtering for roles: {BOOK_SPECIFIC_ROLES}")
            filtered_shifts = [
                s for s in shifts 
                if s.get('role', '') in BOOK_SPECIFIC_ROLES
            ]
            print(f"   {len(filtered_shifts)} shifts match criteria")
            shifts = filtered_shifts
        
        if AUTO_BOOK_ENABLED and shifts:
            print(f"\n📝 Auto-booking enabled...")
            booked_count = 0
            
            for shift in shifts:
                if booked_count >= MAX_SHIFTS_PER_WEEK:
                    print(f"⚠️  Reached max shifts limit ({MAX_SHIFTS_PER_WEEK})")
                    break
                
                if scraper.book_shift(shift.get('id', '')):
                    booked_count += 1
            
            print(f"✓ Booked {booked_count} shifts")
        
        if SYNC_TO_CALENDAR and shifts:
            print(f"\n📆 Syncing to Google Calendar...")
            from backend.google_calendar import GoogleCalendarSync
            
            calendar = GoogleCalendarSync()
            calendar.authenticate()
            calendar.sync_shifts(shifts)
        
        scraper.close()
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure backend modules are available")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✓ AutoShift completed")
    print("=" * 70)


if __name__ == "__main__":
    main()
