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
import sys
import spacy
import os
import msvcrt

# 🔹 Read LinkedIn credentials and Google Sheets Spreadsheet ID from credentials.txt
with open("credentials.txt", "r") as file:
    credentials = {}
    for line in file.readlines():
        line = line.strip() 
        if "=" in line:  
            key, value = line.split("=")
            credentials[key.strip()] = value.strip() 

# 🔹 Check if LinkedIn credentials and Google Sheets Spreadsheet ID are missing
if "username" not in credentials or "password" not in credentials:
    print("⚠️ Missing LinkedIn credentials in credentials.txt")
    sys.exit(1)  

if "spreadsheet_id" not in credentials:
    print("⚠️ Missing Google Sheets Spreadsheet ID in credentials.txt")
    sys.exit(1) 

# 🔹 Google Sheets API Setup
SERVICE_ACCOUNT_FILE = "credentials.json" 
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# 🔹 Authorize Google Sheets API
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# 🔹 Google Sheets: Get Spreadsheet ID from the credentials (read from credentials.txt)
SPREADSHEET_ID = credentials["spreadsheet_id"]  # Get Spreadsheet ID from credentials.txt
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # Select the first sheet

# 🔹 Set Up Selenium WebDriver with WebDriver Manager
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
chrome_options.add_argument("--log-level=3")  # Suppress unnecessary logs
chrome_options.add_argument("--start-maximized")  # Open browser maximized

# Automatically manage ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 10)  

login_success = False  # Flag to track whether login is successful


# 🔹 Open LinkedIn Login Page
def login_to_linkedin():
    global login_success
    driver.get("https://www.linkedin.com/login")

    # 🔹 Log in to LinkedIn
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(credentials["username"])
    password_input = wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(credentials["password"])
    login_button = driver.find_element(By.XPATH, '//*[@type="submit"]')
    login_button.click()

    # 🔹 Wait for CAPTCHA or successful login
    try:
        # Check if CAPTCHA appears (this can vary, customize as needed)
        WebDriverWait(driver, 20).until(EC.url_contains('checkpoint/challenge'))
        print("⚠️ CAPTCHA detected. Please solve it manually...")
        # Wait indefinitely for the user to solve the CAPTCHA
        # Instead of using input(), check the URL directly after some time
        WebDriverWait(driver, 60).until(EC.url_contains('https://www.linkedin.com/feed/'))  # Wait for the feed URL to load
        print("🔹 Successfully logged in! Feed page is accessible.")
        login_success = True
    except TimeoutException:
        # If no CAPTCHA, login was successful
        print(f"Successfully logged in! Current URL: {driver.current_url}")
        # Confirm login by checking for an element that appears only after login (e.g., profile picture)
        try:
            WebDriverWait(driver, 10).until(EC.url_to_be('https://www.linkedin.com/feed/'))
            print("Login confirmed. Feed page is accessible.")
            login_success = True
        except TimeoutException:
            print("⚠️ Login failed. Cannot confirm Feed page.")
            sys.exit(1)

# Try to login
login_to_linkedin()

# 🔹 Wait for LinkedIn Feed to load after solving CAPTCHA
try:
    print("🔹 Waiting for LinkedIn Feed to load...")
    
    # Wait for the feed URL to load (this ensures the page has fully loaded)
    WebDriverWait(driver, 20).until(EC.url_to_be('https://www.linkedin.com/feed/'))  # Wait for the feed URL
    print("🔹 Feed loaded successfully!")

except TimeoutException:
    print("⚠️ Timeout: Could not find the expected element on the page.")
    print("Attempting to check the URL instead...")
    # Optionally, you can check if the URL is 'feed' even if the <main> tag isn't found
    if 'feed' in driver.current_url:
        print("🔹 Feed page detected.")
    else:
        print("⚠️ Something went wrong, could not confirm feed page.")

# 🔹 Open LinkedIn Jobs Page
driver.get("https://www.linkedin.com/jobs/")

# 🔹 XPATH for the Job Title
job_title_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[2]/div/h1/a"

# 🔹 XPATH for the Company Name
company_name_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[1]/div[1]/div/a"

# 🔹 XPATH for the Job Description (where salary is found)
job_desc_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[4]/article/div/div[1]"

# 🔹 XPATH for the Location
location_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span[1]"

# Load spaCy's pre-trained model for NER
nlp = spacy.load("en_core_web_sm")

# Function to extract salary using spaCy (NER)
def extract_salary_with_spacy(job_desc_text):
    try:
        # Process the text with spaCy
        doc = nlp(job_desc_text)
        
        # Look for money-related entities (MONEY, QUANTITY, etc.)
        salary_entities = [ent for ent in doc.ents if ent.label_ in ['MONEY']]
        
        # If we find any money entities, return them
        if salary_entities:
            return " / ".join([ent.text for ent in salary_entities])
        else:
            # Fallback if no entities found
            return "Salary not available"
    except Exception as e:
        print(f"Error using spaCy: {e}")
        return "Salary not available"

# Function to extract location from job description
def extract_location_from_description():
    try:
        # Wait for the location to appear using the provided XPath
        location_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, location_xpath)))
        location = location_element.text.strip()  # Extract and clean the location text

        # Infer remote if location is US
        if "United States" in location:
            location = location.replace("United States", "") + "United States Remote"

        return location if location else "Location not available"
    except Exception as e:
        print(f"Error extracting location: {e}")
        return "Location not available"

# 🔹 Get the current job URL
def get_job_url():
    return driver.execute_script("return window.location.href")

# 🔹 Function to extract salary from the job description
def extract_salary_from_description():
    try:
        # Wait for the job description to appear using the provided XPath
        job_desc_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, job_desc_xpath)))
        job_desc_text = job_desc_element.text.strip()  # Extract and clean the job description text
        print(f"Job Description Text: {job_desc_text}")

        # Extract salary information using spaCy
        salary = extract_salary_with_spacy(job_desc_text)
        
        return salary
    except Exception as e:
        print(f"Error extracting salary from job description: {e}")
        return "Salary not available"
    
def exit_program():
    print("Closing browser...")
    driver.quit()
    os.system('taskkill /f /im chromedriver.exe')
    os.system('taskkill /f /im chrome.exe')
    sys.exit(0)

# 🔹 Loop to continuously monitor the Apply button click
while login_success:
    try:
        if msvcrt.kbhit() and msvcrt.getch().decode().lower() == 'q':
            exit_program()
        
        # Wait for you to click on a job and press Enter in VSCode
        print("🔹 Please click on a job to view details and press Enter when ready...")

        # Wait for the job title to be visible using implicit waits
        job_title_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, job_title_xpath)))
        job_title = job_title_element.text.strip()

        # Wait for the company name to be visible using implicit waits
        company_name_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, company_name_xpath)))
        company_name = company_name_element.text.strip()

        # Capture the current page URL
        job_url = get_job_url()
        print(f"🔎 Job URL: {job_url}")

        # Extract the salary information from the job description
        salary = extract_salary_from_description()
        print(f"💰 Salary: {salary}")

        # Extract the location from the job description
        location = extract_location_from_description()
        print(f"📍 Location: {location}")

        # Save the job details to Google Sheets (Including salary and location)
        if job_title and company_name:
            sheet.append_row([job_title, company_name, job_url, salary, location])
            print(f"✅ Job Saved: {job_title} at {company_name} with Salary: {salary} and Location: {location}")
        else:
            print("⚠️ Job details incomplete, not saving.")

        print("Press 'q' and hit Enter to quit the program or just press Enter to continue: ")

    except Exception as e:
        print(f"⚠️ An error occurred: {str(e)}")

    time.sleep(0.5)
