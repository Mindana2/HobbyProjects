# AutoShift

AutoShift is an automated Python-based bot that securely logs into the PARPAS (SoftAdmin) work schedule portal, scrapes upcoming shifts, and synchronizes them directly with Google Calendar. 

Powered by GitHub Actions, the bot runs completely serverless in the cloud twice a day, ensuring your calendar is always up-to-date without any manual data entry.

## Features

* **Automated Scraping:** Uses Selenium and BeautifulSoup4 to extract all work shifts for the upcoming 30 days.
* **Smart Two-Way Sync:** Automatically inserts new shifts, modifies existing ones if details change, and deletes shifts if you are granted time off or swap a shift.
* **100% Serverless:** Scheduled via a `cron` job in GitHub Actions to run automatically every day at 06:00 and 18:00 UTC (08:00 and 20:00 CEST).

## Tech Stack

* **Language:** Python 3.10+
* **Web Scraping & Automation:** Selenium WebDriver (Headless Chrome), BeautifulSoup4
* **APIs:** Google Calendar API v3 (Google API Client Library)
* **CI/CD & Automation:** GitHub Actions

## How it Works in the Cloud

The project is architected to run entirely in the cloud, removing the need to host it on a personal machine:

1. **GitHub Actions** triggers the workflow twice a day using a scheduled `cron` event.
2. A virtual **Ubuntu runner** is initialized, spinning up a headless Chrome browser.
3. Encrypted login credentials and API tokens are securely injected into the runtime environment via **GitHub Secrets**.
4. The script executes, compares the live portal schedule with your current Google Calendar events, and pushes the necessary diffs (inserts/deletions).

## Security & Configuration

To maintain strict security standards, no passwords, API keys, or access tokens are hardcoded. The project relies entirely on environment variables and encrypted secrets:

| Variable / Secret | Description |
| :--- | :--- |
| `LOGIN_USERNAME` | Your PARPAS portal username |
| `LOGIN_PASSWORD` | Your PARPAS portal password |
| `GOOGLE_CREDENTIALS` | The content of your Google Cloud `credentials.json` |
| `GOOGLE_TOKEN` | The content of your generated `token.json` (OAuth2 user refresh token) |

## Local Development & Setup

If you want to clone this repository and run the script locally on your machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/autoshift.git](https://github.com/yourusername/autoshift.git)
   cd autoshift
