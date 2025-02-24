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


#Global Variables
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

    # 🔹 Wait for login status
    # **Check if CAPTCHA page appears**
    if 'checkpoint/challenge' in driver.current_url:
        print("⚠️ CAPTCHA detected. Please solve it manually...")
        
        # Wait indefinitely for the user to solve the CAPTCHA
        WebDriverWait(driver, 60).until(EC.url_contains('https://www.linkedin.com/feed/'))  # Wait for the feed URL to load
        print("🔹 Successfully logged in! Feed page is accessible.")
        login_success = True

    else:
        # **No CAPTCHA, check if the URL redirects to the feed page**
        if "feed" in driver.current_url:
            print("🔹 Successfully logged in! Redirected to feed page.")
            login_success = True
        else:
            print("⚠️ Login failed. Could not confirm Feed page.")
            # Reload the page and retry the login process
            print("🔄 Reloading the page to try again...")
            driver.refresh()
            # Wait a bit before retrying to allow the page to reload properly
            time.sleep(5)

            # **Return here, so the function can be called again from the outer logic**
            return


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
        location_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, LinkedIn_location_xpath)))
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
        job_desc_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, LinkedIn_job_desc_xpath)))
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

def load_credentials(file_name):
    """ Load specific credentials (LinkedIn or Indeed) from the given file. """
    credentials = {}
    try:
        with open(file_name, "r") as file:
            for line in file.readlines():
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=")
                    credentials[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"⚠️ File {file_name} not found!")
        sys.exit(1)

    # 🔹 Check if LinkedIn credentials and Google Sheets Spreadsheet ID are missing
    if "username" not in credentials or "password" not in credentials:
        print("⚠️ Missing LinkedIn credentials in credentials.txt")
        sys.exit(1)

    if "spreadsheet_id" not in credentials:
        print("⚠️ Missing Google Sheets Spreadsheet ID in credentials.txt")
        sys.exit(1)
    
    return credentials




# 🔹 Main loop to scrape job details and save to Google Sheets
if __name__ == "__main__":
    print("🚀 Starting the LinkedIn Job Application Organizer...")


    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--log-level=3")  
    chrome_options.add_argument("--start-maximized")  

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    credentials = load_credentials("credentialsLinkedin.txt")
    SERVICE_ACCOUNT_FILE = "credentials.json"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    SPREADSHEET_ID = credentials["spreadsheet_id"] 
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # Open the first sheet

    

    Job_Company_Input = input("Linkedin or Indeed? (L or I): ")


    if Job_Company_Input.lower() == 'l':
        print("LinkedIn Selected")
        # 🔹 Read LinkedIn credentials and Google Sheets Spreadsheet ID from credentials.tx
        


        login_to_linkedin()

        # 🔹 Open LinkedIn Jobs Page
        driver.get("https://www.linkedin.com/jobs/")

        LinkedIn_job_title_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[2]/div/h1/a"
        LinkedIn_company_name_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[1]/div[1]/div/a"
        LinkedIn_job_desc_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[4]/article/div/div[1]"
        LinkedIn_location_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span[1]"
        LinkedIn_pay_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div/button/div[1]/span"

        while login_success:

            try:
                # Get current URL before processing
                current_job_url = driver.current_url
            
                # Extract the job ID from the current URL (expected pattern: '...currentJobId=<job_id>&...')
                current_job_id = current_job_url.split('currentJobId=')[-1].split('&')[0]


                # 🔹 Wait for user input to confirm before scraping job data
                user_input = input("Press Enter to save this job or 'q' to quit: ")

                # 🔹 Check for quit command

                if user_input.lower() == 'q':
                    print("Exiting program...")
                    exit_program()  # Exit if 'q' is entered

                # 🔹 Scrape job details after pressing Enter
                job_title = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, LinkedIn_job_title_xpath))
                ).text.strip()

                company_name = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, LinkedIn_company_name_xpath))
                ).text.strip()

                job_desc_text = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, LinkedIn_job_desc_xpath))
                ).text.strip()

                salary_xpath = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, LinkedIn_pay_xpath))
                ).text.strip()

                if not salary_xpath:
                    salary = extract_salary_from_description()
                else:
                    salary = salary_xpath
                

                # 🔹 Extract key information
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
                print(f"⚠️ An error occurred: {str(e)}")
                print(f"Stack trace: {traceback.format_exc()}")

            time.sleep(0.5)  # Brief pause between iterations

    elif Job_Company_Input.lower() == 'i':
        print("Indeed Selected")
        # 🔹 Read Indeed credentials and Google Sheets Spreadsheet ID from credentials.txt
    else:
        print("Invalid Input")
        exit_program()

    


