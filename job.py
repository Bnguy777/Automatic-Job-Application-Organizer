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
import traceback  
from datetime import datetime
import re
import tkinter as tk
from tkinter import messagebox


#Global Variables
login_success = False  

def get_base_path():
    """Get the correct base path whether running as script or exe"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - use EXE's directory
        return os.path.dirname(sys.executable)
    else:
        # Running as script - use script's directory
        return os.path.dirname(os.path.abspath(__file__))
    
# 🔹 Open LinkedIn Login Page
def login_to_linkedin(credentials):
    global login_success
    driver.get("https://www.linkedin.com/login")

    # 🔹 Log in to LinkedIn
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(credentials["username"])
    password_input = wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(credentials["password"])
    login_button = driver.find_element(By.XPATH, '//*[@type="submit"]')
    login_button.click()

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

def login_to_Indeed():
    global login_success
    driver.get("https://www.indeed.com/")

    # 🔹 Wait for the page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    try:
        # 🔹 Check if the search input field is present (indicating the user is logged in)
        search_input = wait.until(EC.presence_of_element_located((By.ID, "text-input-what")))

        if search_input:
            print("🔹 Successfully logged in! Found the search input field.")
            login_success = True
        else:
            print("⚠️ Unable to find the search input field. Login failed.")
            login_success = False
    except Exception as e:
        print(f"⚠️ Error: {e}")
        login_success = False



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
        #print(f"Job Description Text: {job_desc_text}")

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

def load_spacy_model():
    base_path = get_base_path()
    model_path = os.path.join(base_path, 'en_core_web_sm') 
    
    print(f"🔍 Loading spaCy model from: {model_path}")
    print(f"📂 Folder contents: {os.listdir(base_path)}") 
    
    try:
        return spacy.load(model_path)
    except Exception as e:
        print(f"❌ Failed to load spaCy model: {e}")
        print(f"Verify these files exist in {model_path}:")
        print(f"Required: meta.json, config.cfg, tokenizer")
        sys.exit(1)

nlp = load_spacy_model()

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
    credentials = {}
    base_path = get_base_path()
    file_path = os.path.join(base_path, file_name)
    
    print(f"🔍 Looking for credentials at: {file_path}")
    
    try:
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    credentials[key.strip()] = value.strip()
        return credentials
    except FileNotFoundError:
        print(f"❌ Missing {file_name}! Create it in: {base_path}")
        sys.exit(1)

def get_salary(driver):
    try:
        # Use explicit XPath with multiple verification checks
        salary_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((
                By.XPATH,
                '//*[@id="main"]/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div/button/div[1]/span'
            ))
        )
        
        # Direct text extraction with content sanitization
        raw_text = salary_element.get_attribute("textContent").strip()
        
        # Advanced cleaning using regex patterns
        salary = re.sub(
            r'(Matches your job preferences.*|[\n\r\t]+|^\||\|$)', 
            '', 
            raw_text, 
            flags=re.IGNORECASE
        ).strip()
        
        # Final validation checks
        if not re.search(r'\$\d+', salary):
            raise ValueError("No valid salary format found")
            
        #print(f"Sanitized salary: {salary}")
        return salary

    except Exception as e:
        #print(f"Structured salary error: {str(e)}")
        return extract_salary_from_description()  # Fallback to NLP parsing

# 🔹 Main loop to scrape job details and save to Google Sheets
if __name__ == "__main__":
    print("🚀 Starting the LinkedIn Job Application Organizer...")


    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--log-level=3")   
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")  # Add a real User-Agent string
    chrome_options.add_argument("--remote-debugging-port=9222") 

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 10)


    
    #For future implementation when Indeed is supported
    #Job_Company_Input = input("Linkedin or Indeed? (L or I): ")
    Job_Company_Input = 'l'

    if Job_Company_Input.lower() == 'l':

        #print("LinkedIn Selected")

        print("Tracking jobs on LinkedIn...")
        # Load LinkedIn credentials and Google Spreadsheet ID
        linkedin_credentials = load_credentials("credentialsLinkedIn.txt")

        base_path = get_base_path()
        service_account_path = os.path.join(base_path, 'credentials.json')
        
        try:
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(service_account_path, scopes=SCOPES)
            client = gspread.authorize(creds)
            SPREADSHEET_ID = linkedin_credentials["spreadsheet_id"]
            sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        except Exception as e:
            print(f"Error initializing Google Sheets: {e}")
            sys.exit(1)

        
        login_to_linkedin(linkedin_credentials)

        # 🔹 Open LinkedIn Jobs Page
        driver.get("https://www.linkedin.com/jobs/")

        # xpath for job title, company name, job description, location, pay
        LinkedIn_job_title_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[2]/div/h1/a"
        LinkedIn_company_name_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div[1]/div[1]/div[1]/div/a"
        LinkedIn_job_desc_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[4]/article/div/div[1]"
        LinkedIn_location_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span[1]"
        

        while login_success:

            try:

                current_job_url = driver.current_url
                current_job_id = current_job_url.split('currentJobId=')[-1].split('&')[0]

                user_input = input("Press Enter to save this job or 'q' to quit: ")

                if user_input.lower() == 'q':
                    print("Exiting program...")
                    exit_program()  

                job_title = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, LinkedIn_job_title_xpath))
                ).text.strip()

                company_name = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, LinkedIn_company_name_xpath))
                ).text.strip()

                job_desc_text = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, LinkedIn_job_desc_xpath))
                ).text.strip()

                salary = get_salary(driver)

                if not salary:
                    salary = "N/A"

                
                

                # 🔹 Extract key information
                location = extract_location_from_description()
                benefits = extract_important_benefits(job_desc_text)
                job_url = driver.current_url

                # 🔹 Save to Google Sheets with organized columns
                if job_title and company_name:
                    base_row = [job_title, company_name, "", salary, location]
                    sheet.append_row(base_row)
                    
                    row_num = len(sheet.get_all_values())

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

            time.sleep(0.5)  

    elif Job_Company_Input.lower() == 'i':
        print("Indeed Selected")
        print("Indeed is currently not supported.")
        
        # Currently not supported. Can not get through captcha manually

        '''
        credentials = load_credentials("credentialsIndeed.txt")
        SERVICE_ACCOUNT_FILE = "credentials.json"
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)

        SPREADSHEET_ID = credentials["spreadsheet_id"] 
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1 
        
        login_to_Indeed()
        print("t12")
        driver.get("https://www.indeed.com/")
        print("t12")
        print(login_success)
        while login_success:

            try:
                print("t13")
                current_job_url = driver.current_url
                current_job_id = current_job_url.split('currentJobId=')[-1].split('&')[0]

                user_input = input("Press Enter to save this job or 'q' to quit: ")

                if user_input.lower() == 'q':
                    print("Exiting program...")
                    exit_program()
            except Exception as e:
                print(f"⚠️ An error occurred: {str(e)}")
                print(f"Stack trace: {traceback.format_exc()}")

            time.sleep(0.5)  
    '''


        
    elif Job_Company_Input.lower() == 'm':
        print("Manual Input Selected")
    else:
        print("Invalid Input")
        exit_program()

    


