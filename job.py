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
from spacy.matcher import Matcher
import os
import msvcrt
import traceback  # Added for better exception logging
from datetime import datetime
import re

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

    # 🔹 Enter credentials and log in
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(credentials["username"])
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(credentials["password"])
    driver.find_element(By.XPATH, '//*[@type="submit"]').click()

    # 🔹 Simultaneous check for CAPTCHA or successful login
    try:
        WebDriverWait(driver, 20).until(
            lambda d: 'checkpoint/challenge' in d.current_url or d.find_elements(By.CSS_SELECTOR, "img.global-nav__me-photo")
        )
    except TimeoutException:
        print("⛔ Login failed - Timeout waiting for CAPTCHA or login confirmation")
        sys.exit(1)

    # 🔹 Determine which condition was met
    if 'checkpoint/challenge' in driver.current_url:
        print("⚠️ CAPTCHA detected. Please solve manually within 60 seconds...")
        try:
            WebDriverWait(driver, 60).until(
                EC.url_contains('feed')  # Wait for successful redirect after CAPTCHA
            )
            login_success = True
            print("✅ CAPTCHA solved! Login successful")
        except TimeoutException:
            print("⛔ CAPTCHA resolution timed out")
            sys.exit(1)
    else:
        try:
            # Quick confirmation check for profile element
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "img.global-nav__me-photo"))
            )
            login_success = True
            print("✅ Logged in successfully without CAPTCHA")
        except TimeoutException:
            print("⛔ Login verification failed - Profile element not found")
            sys.exit(1)

    print(f"Login status: {login_success}")


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
    sys.exit(0)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Configure benefit patterns with linguistic context
benefit_patterns = [
    # Health insurance variations
    [{"LEMMA": {"IN": ["medical", "dental", "vision"]}}, {"LEMMA": "insurance"}],
    [{"LOWER": "health"}, {"LOWER": {"IN": ["coverage", "plan"]}}],
    
    # Financial benefits
    [{"LOWER": "401"}, {"LOWER": "k"}],
    [{"LEMMA": "retirement"}, {"LEMMA": "plan"}],
    [{"LOWER": "pension"}],
    
    # Time off
    [{"LEMMA": "paid"}, {"LEMMA": {"IN": ["leave", "time"]}}, {"LEMMA": "off"}],
    [{"LOWER": "pto"}],
    
    # Flexible accounts
    [{"LOWER": "fsa"}],
    [{"LOWER": "hsa"}],
    
    # Education & development
    [{"LEMMA": "tuition"}, {"LEMMA": "reimbursement"}],
    [{"LEMMA": "professional"}, {"LEMMA": "development"}],
    
    # Workplace arrangements
    [{"LEMMA": "remote"}, {"LEMMA": "work"}],
    [{"LEMMA": "flexible"}, {"LEMMA": "schedule"}]
]

matcher = Matcher(nlp.vocab)
for pattern in benefit_patterns:
    matcher.add("BENEFIT_PATTERNS", [pattern])

def extract_important_benefits(job_desc_text):
    doc = nlp(job_desc_text.lower())
    benefits = set()

    # Pattern-based matching
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        benefits.add(span.text.title())

    # Contextual extraction for compensation phrases
    money_phrases = ["match", "contribution", "bonus", "stock", "equity"]
    for sent in doc.sents:
        if any(token.text in money_phrases for token in sent):
            benefits.add(sent.text.capitalize())

    # Standardize similar terms
    benefits = {b.replace("Pto", "Paid Time Off") for b in benefits}
    benefits = {b.replace("401 K", "401(k)") for b in benefits}

    return ", ".join(sorted(benefits))[:500] if benefits else "Key benefits not specified"

# 🔹 Loop to continuously monitor jobs
max_retries = 5
retries = 0
previous_job_id = None  # Track last processed job ID

while login_success and retries < max_retries:
    try:
        # Get current URL before processing
        current_job_url = driver.current_url
        
        # Extract the job ID from the current URL
        current_job_id = current_job_url.split('currentJobId=')[-1].split('&')[0]  # Assuming the URL follows the pattern

        # 🔄 Check if the job ID has changed
        if current_job_id == previous_job_id:
            retries += 1
            print(f"⚠️ Same job detected. Retry {retries}/{max_retries}. Please select a new job.")
            if retries >= max_retries:
                print("🚫 Maximum retries reached. Exiting...")
                break
            time.sleep(2)  # Add delay to avoid rapid looping
            continue  # Skip to next iteration
        else:
            retries = 0  # Reset counter for new job
            previous_job_id = current_job_id  # Update tracked job ID

        # 🔹 Wait for user input to confirm before scraping job data
        user_input = input(f"Job found: {current_job_url}\nPress Enter to save this job or 'q' to quit: ")

        # 🔹 Check for quit command

        if user_input.lower() == 'q':
            print("Exiting program...")
            exit_program()  # Exit if 'q' is entered

        # 🔹 Scrape job details after pressing Enter
        job_title = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, job_title_xpath))
        ).text.strip()

        company_name = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, company_name_xpath))
        ).text.strip()

        job_desc_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, job_desc_xpath))
        ).text.strip()

        # 🔹 Extract key information
        salary = extract_salary_from_description()
        location = extract_location_from_description()
        benefits = extract_important_benefits(job_desc_text)
        job_url = driver.current_url

        # 🔹 Save to Google Sheets with organized columns
        if job_title and company_name:
            # Append base row structure
            base_row = [job_title, company_name, "", salary, location]
            sheet.append_row(base_row)
            
            # Get new row number
            row_num = len(sheet.get_all_values())

            # Update specific columns
            updates = {
                3: f'=HYPERLINK("{job_url}", "Link")', 
                6: datetime.today().strftime('%m/%d/%y'),  
                8: benefits,  
                7: "Waiting" 
            }

            for col, value in updates.items():
                sheet.update_cell(row_num, col, value)

            print(f"✅ Job Saved: {job_title} at {company_name}")

    except Exception as e:
        retries += 1
        print(f"⚠️ An error occurred: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        if retries >= max_retries:
            print("🚫 Maximum error retries reached, exiting...")
            break

    time.sleep(0.5)  # Brief pause between iterations
