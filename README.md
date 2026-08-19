# AI Lead Discovery & Cold Email Generator 

An end-to-end, AI-powered pipeline designed to automate the B2B lead generation and outreach workflow. The application ingests lead lists, extracts target domain intelligence, scrapes company websites for context, generates highly tailored cold emails using Large Language Models (LLMs), and syncs all outputs directly to Google Sheets.

---

## Key Features

* **Lead Ingestion & Cleaning:** Reads raw lead datasets (CSV) and normalizes contact/company input fields.
* **Domain & Company Discovery:** Resolves target web domains and retrieves enriched company metadata.
* **Contextual Web Scraping:** Scrapes live website content to extract contextual information about target brands.
* **AI Cold Email Generation:** Leverages OpenRouter API (LLMs) to construct highly personalized, context-aware email templates tailored to each lead.
* **Google Sheets Integration:** Automatically writes processed leads, company insights, and generated emails to a Google Sheet in real time.
* **Robust Logging & Error Handling:** Includes centralized exception management with automated logging to track application runs.

---

## Tech Stack

* **Language:** Python 3.12+
* **AI / LLM Orchestration:** OpenRouter API
* **Integrations:** Google Sheets API (`gspread` / Google API Client)
* **Web Scraping:** BeautifulSoup4 / Requests
* **Data Handling:** Pandas

---

## Repository Structure

```text
.
├── credentials/
│   └── google_credentials.json.example  # Service account template
├── data/
│   ├── leads.csv                        # Primary lead input dataset
│   └── sample_leads.csv                 # Sample dataset for testing
├── src/
│   ├── ai_summarizer.py                 # Summarizes web scrape data via AI
│   ├── company_discovery.py             # Company background & metadata lookup
│   ├── config.py                        # Configuration and environment loader
│   ├── domain_extraction.py             # Domain parsing logic
│   ├── email_generator.py               # Dynamic prompt engineering & email generation
│   ├── error_handler.py                 # Centralized logging & error tracking
│   ├── lead_discovery.py                # Lead search and target identification
│   ├── lead_ingestion.py                # Data loading and preprocessing pipeline
│   ├── main.py                          # Pipeline entry point
│   ├── sheets_integration.py            # Google Sheets API workflow handler
│   └── website_scraper.py               # Web scraping engine for site context
├── tests/
│   ├── test_openrouter.py               # OpenRouter API connectivity tests
│   ├── test_scraper.py                  # Unit tests for the web scraper
│   └── test_sheets.py                   # Unit tests for Google Sheets integration
├── .env.example                         # Environment variable template
├── requirements.txt                     # Python dependencies
└── README.md

```

---

## Quick Start

### 1. Prerequisites

* **Python 3.12** or higher installed.
* An **OpenRouter API Key** for AI model access.
* A **Google Cloud Platform (GCP) Service Account** with the Google Sheets API enabled.

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
# Clone the repository
git clone https://github.com/riteshdarji04/Lead_Gen.git
cd your-repo-name

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

```

### 3. Environment & Credentials Setup

1. **Environment Variables:**
Copy the `.env.example` file to create your `.env` file:
```bash
cp .env.example .env

```


Open `.env` and add your credentials:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
GOOGLE_SHEETS_SPREADSHEET_ID=your_google_sheet_id_here

```


2. **Google Service Account:**
Place your Google Service Account JSON key inside the `credentials/` folder and name it `google_credentials.json`. Ensure you share your target Google Sheet with the `client_email` address found inside that JSON file.

---

## Running the Application

### Execute the Main Pipeline

Place your lead data in `data/leads.csv` and run:

```bash
python -m src.main

```

---

## 📝 Logging & Monitoring

All pipeline activities, warnings, and error logs are saved automatically to the local log directory at `data/logs/processing.log` for easy debugging and audit tracking.
