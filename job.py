import time
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import signal
import sys

# 🔹 Google Sheets API Setup
SERVICE_ACCOUNT_FILE = "credentials.json"  # Path to Google API key file
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_ID = "101wYtyRRTlB0FKWzFn7jYuRiRV93tkQOiP7N0WAqqUM"  # Your Google Sheet ID
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # Select the first sheet

# 🔹 Read LinkedIn credentials from file
with open("credentials.txt", "r") as file:
    lines = file.readlines()
    credentials = {}
    for line in lines:
        key, value = line.strip().split("=")
        credentials[key.strip()] = value.strip()  # Strip spaces from key and value

# 🔹 Check if credentials are missing
if "username" not in credentials or "password" not in credentials:
    print("⚠️ Missing username or password in credentials.txt")
    sys.exit(1)  # Exit if credentials are not found

# 🔹 Set Up Selenium WebDriver with WebDriver Manager
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
chrome_options.add_argument("--log-level=3")  # Suppress unnecessary logs
chrome_options.add_argument("--start-maximized")  # Open browser maximized

# Automatically manage ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)  # Increased timeout to 20 seconds

# 🔹 Open LinkedIn Login Page
driver.get("https://www.linkedin.com/login")

# 🔹 Log in to LinkedIn
username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
username_input.send_keys(credentials["username"])
password_input.send_keys(credentials["password"])
login_button = driver.find_element(By.XPATH, '//*[@type="submit"]')
login_button.click()

# 🔹 Verify successful login by checking the current URL
print(f"Successfully logged in! Current URL: {driver.current_url}")

# 🔹 Wait for LinkedIn Feed to load (use a more generic element 'main')
try:
    print("🔹 Waiting for LinkedIn Feed to load...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))  # Waiting for 'main' tag to load
    print("🔹 Feed loaded successfully!")
except TimeoutException:
    print("⚠️ Timeout: Could not find the expected element on the page.")

# 🔹 Open LinkedIn Jobs Page
driver.get("https://www.linkedin.com/jobs/")

# 🔹 XPATH for the Job Title
job_title_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[2]/div/h1/a"

# 🔹 XPATH for the Company Name
company_name_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[1]/div[1]/div/a"

# 🔹 Get the current job URL
def get_job_url():
    return driver.execute_script("return window.location.href")

# 🔹 Signal handler for clean exit on Escape key press
def signal_handler(sig, frame):
    print("\n🔴 Exiting the program...")
    driver.quit()  # Make sure to quit the browser before exiting
    sys.exit(0)

# Bind the signal to catch the Escape key and exit
signal.signal(signal.SIGINT, signal_handler)

# 🔹 Loop to continuously monitor the Apply button click
while True:
    try:
        # Wait for you to click a job and press Enter in VSCode
        print("🔹 Please click on a job to view details and press Enter when ready...")

        # Wait for you to press Enter to proceed
        input("Press Enter here when you're on the job details page...")

        # Wait for the job title to be visible using implicit waits
        job_title_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, job_title_xpath)))
        job_title = job_title_element.text.strip()

        # Wait for the company name to be visible using implicit waits
        company_name_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, company_name_xpath)))
        company_name = company_name_element.text.strip()

        # Capture the current page URL
        job_url = get_job_url()
        print(f"🔎 Job URL: {job_url}")

        # Save the job details to Google Sheets
        if job_title and company_name:
            sheet.append_row([job_title, company_name, job_url])
            print(f"✅ Job Saved: {job_title} at {company_name}")
        else:
            print("⚠️ Job details incomplete, not saving.")

    except Exception as e:
        print(f"⚠️ An error occurred: {str(e)}")

    # Check if Escape was pressed (you can manually exit by pressing 'Ctrl + C' in the terminal)
    print("🔹 Press 'Ctrl + C' to exit.")
    time.sleep(0.5)  # Reduced delay to speed up the loop
