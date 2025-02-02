---

```markdown
# Automatic Job Application Tracker & Organizer 🚀

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Automatically log LinkedIn job applications to Google Sheets** with one keystroke. Perfect for high-volume job seekers!  
*(No more manual copy-pasting!)*

---

## 🔍 Overview
### **Problem**
Tracking hundreds of job applications manually is tedious and error-prone. This tool solves:
- **Repetitive data entry** for job titles, companies, and URLs
- **Disorganized tracking** of application statuses and follow-ups
- **No centralized system** for analyzing application success rates

### **Solution**
A script that **automatically logs LinkedIn job details to Google Sheets** with one keystroke.  
**Currently tracked**:
- Job Title
- Company Name
- Application URL
- Application Date (auto-generated)

---

## 🛠️ Features
| Feature                | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **LinkedIn Scraping**  | Captures job details directly from LinkedIn listings                       |
| **Google Sheets Sync** | Real-time updates to your centralized tracker                              |
| **One-Key Workflow**   | Press `Enter` to log jobs after applying                                   |
| **Customizable**       | Easily add/remove columns in Google Sheets (e.g., Salary, Status)          |

---

## ⚙️ Installation
1. **Clone the repo**:
   ```bash
   git clone https://github.com/yourusername/job-application-tracker.git
   cd job-application-tracker
   ```
2. **Set up Google Sheets API** ([guide](https://developers.google.com/sheets/api/quickstart/python)) and save credentials as `credentials.json`
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage
1. **Apply to a job on LinkedIn**.
2. **Run the script**:
   ```bash
   python tracker.py
   ```
3. **Press `Enter`** to log the job details automatically.  

![Demo](demo.gif) *← Add a workflow GIF here*

---

## 🌟 Future Directions & Roadmap
### **Core Features**
- [ ] **Track Application Status**: Add columns for `Interview Scheduled`, `Rejected`, `Offer Received`
- [ ] **Benefits Logging**: Auto-capture or manually input health insurance, PTO, etc.
- [ ] **PostgreSQL Integration**: Optional database backend for advanced querying
- [ ] **GUI Customization**: Checkboxes to toggle tracked fields (e.g., Salary, Benefits)

### **Advanced Features**
- [ ] **Auto-Classification**: Use AI to categorize jobs by seniority/industry
- [ ] **Analytics Dashboard**: Visualize metrics like response rates and success trends
- [ ] **LinkedIn Bot**: Automate application submissions (where permitted)

---

## 🤝 Contributing
1. Fork the repo
2. Create a branch: `git checkout -b feature/your-idea`
3. Test changes locally
4. Submit a PR with a clear description. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.

---

*Built by [Your Name](https://github.com/yourusername) to combat job-hunting chaos.*  
*Need help? [Open an Issue](https://github.com/yourusername/job-application-tracker/issues).*
```

---