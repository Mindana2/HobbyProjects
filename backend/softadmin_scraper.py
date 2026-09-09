from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

STOCKHOLM_TZ = ZoneInfo("Europe/Stockholm")


class softadmin_scraper():
    def __init__(self):
        service = Service()
        self.options = webdriver.ChromeOptions()

        # Hindrar att browsern stängs direkt
        ##self.options.add_experimental_option("detach", True)

        self.options.add_argument("--headless=new")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920,1080")

        # Driver
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.login_url = "https://parpas.parksandresorts.com/admin/Login.aspx?languageid=1"

    def _make_datetime(self, date_str, time_str):
        """Build an ISO-8601 datetime string with the correct Stockholm UTC offset."""
        dt = datetime.fromisoformat(f"{date_str}T{time_str}:00").replace(tzinfo=STOCKHOLM_TZ)
        # astimezone keeps the instant, formats with the right +HH:MM offset
        return dt.isoformat()

    def login(self, username, password):
        self.driver.get(self.login_url)

        username_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "UsernameTextBox")))
        password_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "PasswordTextBox")))
        login_submit = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "LoginSubmit")))

        username_input.send_keys(username)
        password_input.send_keys(password)
        login_submit.click()

    def fetch_schedule(self):

        # Tryck på "Mitt personalkort"
        staff_card = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@data-sa-minimized-tooltip='Mitt personalkort']")))
        staff_card.click()

        # Kliv in i iframes på startsidan
        iframe_element1 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@id='RightFrameRoot' and @class='saRightFrameRoot']")))
        self.driver.switch_to.frame(iframe_element1)
        iframe_element2 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@id='Right' and @class='saRightFrame']")))
        self.driver.switch_to.frame(iframe_element2)

        # Tryck på "Visa schema"
        schedule_buttton = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Visa schema')]")))
        schedule_buttton.click()

        # Kliv in i iframes på schemasidan
        self.driver.switch_to.default_content()
        iframe_element3 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@id='RightFrameRoot' and @class='saRightFrameRoot']")))
        self.driver.switch_to.frame(iframe_element3)
        iframe_element4 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@id='Right' and @class='saRightFrame']")))
        self.driver.switch_to.frame(iframe_element4)

        # Gå in i kalender
        week_elements = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='saWeek']")))

        rows = []

        for week in week_elements:
            soup = BeautifulSoup(week.get_attribute('innerHTML'), features='html.parser')
            days_all = soup.find_all('div', 'saDateInner')

            for day in days_all:
                description = day.find('div', 'saActivityDescription')
                activity = day.select('li.saActivity:not(.saAllDay)')
                date = day.find('time')['datetime']

                # Both description AND activity must be present to form a valid shift row
                if description is not None and activity:
                    parts = description.contents[0].split()
                    starttime = self._make_datetime(date, parts[0])
                    endtime = self._make_datetime(date, parts[2])
                    status = description.contents[4].string
                    func = activity[0].find('div', 'saActivityHeading').string

                    rows.append({
                        'function': func,
                        'starttime': starttime,
                        'endtime': endtime,
                        'status': status,
                    })

        self.df = pd.DataFrame(rows, columns=['function', 'starttime', 'endtime', 'status'])
        self.df.to_csv('schema.csv')

        return self.df

    def quit(self):
        self.driver.quit()
