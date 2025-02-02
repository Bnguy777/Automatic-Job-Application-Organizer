# Automatic Job Application Tracker & Organizer 🚀

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Automatically log LinkedIn job applications to Google Sheets** with one keystroke. Perfect for high-volume job seekers!  
*(No more manual copy-pasting!)*

---

## 🔍 Overview
### **Problem**
Job hunting often means **hundreds of applications** spread across platforms. Manually tracking:
- Job titles
- Company names
- Application URLs
- Status updates  
...becomes **error-prone and time-consuming**. This tool automates the tedious parts so you can focus on landing roles.

### **Solution**
A lightweight automation script that:
1. **Scrapes job details** from LinkedIn listings
2. **Auto-populates** a Google Sheet with:
   - Job Title
   - Company Name
   - Application URL
   - Application Date *(automatically logged)*
3. **One-key workflow** – press `Enter` to log jobs after applying

---

## 🛠️ Features
| Feature                | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **LinkedIn Integration** | Auto-captures job details from LinkedIn listings                           |
| **Google Sheets Sync**   | Updates your tracker in real-time                                         |
| **Minimal Input**        | Log entries with a single keystroke                                       |
| **Customizable Fields**  | Add/remove columns in your Sheet (e.g., Status, Salary)                   |

---

## ⚙️ Installation

### Prerequisites
- Google Account (for Sheets)
- LinkedIn account (logged in during use)
- Python 3.8+ *(if using a Python script)*

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/job-application-tracker.git
   cd job-application-tracker