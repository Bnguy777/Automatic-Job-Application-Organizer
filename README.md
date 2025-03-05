# 🔍 Automated Job Application Tracker & Organizer <a name="overview"></a>

**Never miss a job application detail again!** Seamlessly sync LinkedIn job postings to your personalized Google Sheet tracker with AI-powered data extraction.

[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Open Issues](https://img.shields.io/github/issues/Bnguy777/Automatic-Job-Application-Organizer)](https://github.com/Bnguy777/Automatic-Job-Application-Organizer/issues)

![Demo Banner](https://via.placeholder.com/1200x400.png?text=Google+Sheets+Integration+Demo+Showing+Job+Details+Tracking)

---

## 🛠️ Features <a name="features"></a>

| Feature                | Implementation Details                                                                 |
|------------------------|---------------------------------------------------------------------------------------|
| **Google Sheet Sync**  | Real-time updates via Sheets API v4 with automatic formatting                         |
| **LinkedIn Parsing**   | CSS Selector-based extraction of job titles, companies, and salaries                 |

---

## ⚙️ Installation Guide <a name="installation"></a>

### 1. Google Sheet Setup (MANDATORY)
**Step 1:** [Make a Copy of Template Sheet](https://docs.google.com/spreadsheets/d/1jEu5SZAC8szJa9HBLkUzjHBen_NDxcdvQIMF1tHI88Q/copy)  
**Step 2:** Share with Service Account:
```python
# Find in credentials.json:
"client_email": "your-service-account@project-id.iam.gserviceaccount.com"

# In Google Sheet: Share > Add email > Editor access
```

### 2. Google Cloud Configuration
1. Create Project: [console.cloud.google.com](https://console.cloud.google.com/)
2. Enable APIs:
   ```bash
   gcloud services enable sheets.googleapis.com drive.googleapis.com
   ```
3. Create Service Account:
   ```bash
   gcloud iam service-accounts create job-tracker \
     --display-name="Job Application Tracker"
   ```
4. Download JSON Credentials → Rename to `credentials.json`

### 3. Local Environment Setup
```bash
# Clone repository
git clone https://github.com/Bnguy777/Automatic-Job-Application-Organizer.git
cd Automatic-Job-Application-Organizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize NLP model
python -m spacy download en_core_web_sm
```

### 4. Credential Files Setup
**credentialsLinkedIn.txt** (UTF-8 Encoding Required):
```plaintext
[Authentication]
email = your.linkedin@email.com
password = YourSecurePassword123!
spreadsheet_id = your-copied-sheet-id-from-url

[Settings]
headless_mode = False  # Set True for server environments
max_retries = 5
```

**File Structure Validation**:
```
.
├── credentials.json            # Google Service Account
├── credentialsLinkedIn.txt     # User-specific settings
├── JobOrganizer.exe            # Main file to run
├── chromedriver.exe            # Platform-specific drivers
├── en_core_web_sm/             # NLP model data
```

---

## 🚀 Usage Instructions <a name="usage"></a>

```bash
# Start application (ensure Chrome is installed)
python job.py

# Command List:
# [ENTER]  - Log current job
# [Q]      - Quit and save session
```

**First-Run Workflow**:
1. Complete LinkedIn CAPTCHA (if prompted)
2. Grant OAuth permissions for Google Sheets
3. Begin logging jobs via terminal interface

![Terminal Interface Demo](https://via.placeholder.com/600x300.png?text=Terminal+Interface+Showing+Job+Logging+Commands)

---

## 🖥️ Live Demo <a name="demo"></a>

### Google Sheet Integration
[![Google Sheet Demo](https://via.placeholder.com/800x400.png?text=Live+Google+Sheet+Showing+Real-Time+Job+Application+Updates)](https://youtu.be/TMxOaq1Oj1g)

**Tracked Fields**:
1. Job Title (with NLP normalization)
2. Company Name (with Fortune 500 flagging)
3. Application URL (direct LinkedIn deep link)
4. Salary Range (converted to USD equivalents)
5. Application Status Pipeline:
   ```mermaid
   graph LR
   A[Discovered] --> B[Applied]
   B --> C[Interviewing]
   C --> D[Offer]
   C --> E[Rejected]
   ```

---

## 🌟 Roadmap & Future Features <a name="roadmap"></a>

### Core Functionality
- [x] **v1.0 Base Functionality** 
- [x] **EXE Packaging** 
- [ ] **v2.0 Multi-Platform Support** 
  - Indeed.com integration
  - Glassdoor scraping

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for full text.

---

> **Note**: Requires active LinkedIn account and Google Workspace-compatible account.  
> 🌐 GitHub: [https://github.com/Bnguy777](https://github.com/Bnguy777)
