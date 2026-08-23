import dotenv
from os import environ
from pathlib import Path
from backend.softadmin_scraper import softadmin_scraper
from backend.google_calendar import google_calendar


def main():
    # Load .env FIRST so all env vars are available before constructing objects
    current_dir = Path(__file__).resolve().parent
    env_path = current_dir / '.env'
    dotenv.load_dotenv(dotenv_path=env_path)

    username = environ.get("LOGIN_USERNAME")
    password = environ.get("LOGIN_PASSWORD")

    scr = softadmin_scraper()
    cal = google_calendar()

    try:
        scr.login(username, password)
        df_schedule = scr.fetch_schedule()
    finally:
        # The 'finally' block is guaranteed to run,
        # even if the code above crashes with an error!
        # Manual close driver: taskkill /f /im chromedriver.exe
        print("Cleaning up driver processes...")
        scr.quit()

    cal.sync_dataframe(df_schedule)


if __name__ == "__main__":
    main()
