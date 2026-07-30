"""
config.py - Central Configuration File
======================================
All project constants, settings, and configurations in one place.
Load from environment variables using .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Get the root directory of the project
PROJECT_ROOT = Path(__file__).parent.parent

# Define all paths
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"
OUTPUT_DIR = DATA_DIR / "output"
SRC_DIR = PROJECT_ROOT / "src"

# Create directories if they don't exist
CREDENTIALS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# File paths
GOOGLE_CREDENTIALS_FILE = CREDENTIALS_DIR / "google_credentials.json"
LOG_FILE = LOGS_DIR / "processing.log"
SAMPLE_CSV = DATA_DIR / "sample_leads.csv"
OUTPUT_CSV = OUTPUT_DIR / "results.csv"


# ============================================================================
# OPENROUTER API CONFIGURATION
# ============================================================================

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "not_set"
)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models for different tasks
OPENROUTER_MODEL_SUMMARY = os.getenv(
    "OPENROUTER_MODEL_SUMMARY",
    "google/gemma-4-31b-it:free"  # For website summarization
)

OPENROUTER_MODEL_EMAIL = os.getenv(
    "OPENROUTER_MODEL_EMAIL",
    "tencent/hy3:free"  # For email generation
)

# Backup models if primary fails
OPENROUTER_MODEL_SUMMARY_BACKUP = os.getenv(
    "OPENROUTER_MODEL_SUMMARY_BACKUP",
    "nvidia/nemotron-3-ultra-550b-a55b:free"
)

OPENROUTER_MODEL_EMAIL_BACKUP = os.getenv(
    "OPENROUTER_MODEL_EMAIL_BACKUP",
    "google/gemma-4-26b-a4b-it:free"
)


# ============================================================================
# GOOGLE SHEETS CONFIGURATION
# ============================================================================

GOOGLE_CREDENTIALS_PATH = str(GOOGLE_CREDENTIALS_FILE)

GOOGLE_SHEET_ID = os.getenv(
    "GOOGLE_SHEET_ID",
    "not_set"
)

GOOGLE_SHEET_NAME = os.getenv(
    "GOOGLE_SHEET_NAME",
    "Leads"
)

# Google Sheets API scopes
GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


# ============================================================================
# APIFY API CONFIGURATION (Scenario 2: Auto Lead Discovery)
# ============================================================================

# Apify API token - get from https://console.apify.com/account/integrations
APIPY_API_TOKEN = os.getenv(
    "APIFY_API_TOKEN",
    "not_set"
)

# Apify actor for company discovery (Google Maps / business scraper)
APIPY_ACTOR_ID = os.getenv(
    "APIFY_ACTOR_ID",
    "compass/crawler-google-places"
)

# Apify base URL
APIPY_BASE_URL = "https://api.apify.com/v2"

# Apify run timeout (seconds) - actor runs are async
APIPY_RUN_TIMEOUT = int(os.getenv("APIFY_RUN_TIMEOUT", "300"))  # 5 minutes


# ============================================================================
# PROJECT SETTINGS
# ============================================================================

# Maximum number of leads to process per batch
MAX_LEADS_PER_BATCH = int(os.getenv("MAX_LEADS_PER_BATCH", "100"))

# Website scraping timeout (seconds)
WEBSITE_TIMEOUT_SECONDS = int(os.getenv("WEBSITE_TIMEOUT_SECONDS", "10"))

# Maximum characters to extract from website
MAX_WEBSITE_CONTENT_LENGTH = 5000

# Delay between requests (seconds) - be respectful to servers
REQUEST_DELAY = 1.0

# Maximum retries for failed requests
MAX_RETRIES = 3

# User agent for web requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36"
)


# ============================================================================
# AI/LLM PROMPTS
# ============================================================================

# System prompt for summarization task
SUMMARY_SYSTEM_PROMPT = """You are an expert at analyzing company websites and creating concise business summaries.
Your task is to read website content and provide a 2-3 sentence summary that clearly describes:
1. What the company does
2. Their main products/services
3. Their target market or use case

Be factual and precise. If information is unclear, say so."""

# System prompt for email generation task
EMAIL_SYSTEM_PROMPT = """You are an expert at writing personalized B2B outreach emails in HTML.
Your task is to generate a complete HTML email that:
1. Is personalized to the company's specific business
2. Explains how our AI services can help them
3. Includes a professional call-to-action button
4. Is well-formatted HTML with inline styles
5. Has proper structure with body tags

CRITICAL: Return ONLY HTML code. No markdown. No backticks. No explanation. Just HTML."""

# Prompt template for summarization
SUMMARY_PROMPT_TEMPLATE = """
Please summarize the following website content for a company in 2-3 sentences. 
Focus on what the company does and their main business.

Company Name: {company_name}
Website Content:
{website_content}

Summary:
"""

# Prompt template for email generation
EMAIL_PROMPT_TEMPLATE = """
Generate a professional B2B outreach email for the following company in COMPLETE HTML format:

Company Name: {company_name}
Industry: {industry}
Company Size: {company_size}
Business Summary: {business_summary}

Our AI Services:
- We help companies automate their business processes using AI
- We provide custom AI solutions for data processing, analysis, and automation
- We specialize in solving complex business problems with machine learning

IMPORTANT: Return ONLY valid HTML email. No markdown. No code blocks. No backticks.

Start with <html> and end with </html>. Include:
1. Professional greeting with company name
2. 2-3 sentences about their business (reference the summary)
3. How our AI services help them specifically
4. A clear CTA button with link
5. Professional signature

Make it friendly but professional. 150-250 words.
"""


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Debug mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


# ============================================================================
# OPENROUTER API HEADERS
# ============================================================================

def get_openrouter_headers():
    """Get headers for OpenRouter API requests"""
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/ai-lead-gen-project",
        "X-Title": "AI Lead Generation Bot",
    }


# ============================================================================
# VALIDATION CHECKS
# ============================================================================

def validate_configuration():
    """
    Validate that all required configurations are set.
    Raise error if critical settings are missing.
    """
    errors = []
    warnings = []
    
    # Critical checks
    if OPENROUTER_API_KEY == "not_set":
        errors.append("❌ OPENROUTER_API_KEY not set in .env file")
    
    if GOOGLE_SHEET_ID == "not_set":
        errors.append("❌ GOOGLE_SHEET_ID not set in .env file")
    
    if not GOOGLE_CREDENTIALS_FILE.exists():
        errors.append(
            f"❌ Google credentials file not found at: {GOOGLE_CREDENTIALS_FILE}"
        )
    
    # Warnings
    if APIPY_API_TOKEN == "not_set":
        warnings.append(
            "ℹ️  APIFY_API_TOKEN not set — Scenario 2 (auto lead discovery) will be disabled. "
            "Set it in .env if you want to use --source auto."
        )
    
    if WEBSITE_TIMEOUT_SECONDS < 5:
        warnings.append(
            "⚠️  WEBSITE_TIMEOUT_SECONDS is very low (< 5 seconds). "
            "Websites might not load properly."
        )
    
    if MAX_LEADS_PER_BATCH > 500:
        warnings.append(
            "⚠️  MAX_LEADS_PER_BATCH is very high (> 500). "
            "Consider processing in smaller batches."
        )
    
    # Report errors
    if errors:
        print("\n" + "="*60)
        print("CONFIGURATION ERRORS - PLEASE FIX:")
        print("="*60)
        for error in errors:
            print(error)
        print("="*60 + "\n")
        raise ValueError("Critical configuration errors detected.")
    
    # Report warnings
    if warnings:
        print("\n" + "="*60)
        print("CONFIGURATION WARNINGS:")
        print("="*60)
        for warning in warnings:
            print(warning)
        print("="*60 + "\n")
    
    return True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sample_leads_data():
    """
    Return sample leads data for testing
    """
    return [
        {
            "company_name": "TechStartup Inc",
            "email": "contact@techstartup.com",
            "website": "https://techstartup.com",
            "industry": "Healthcare",
        },
        {
            "company_name": "DataCorp Solutions",
            "email": "hello@datacorp.com",
            "website": "https://datacorp.com",
            "industry": "Finance",
        },
        {
            "company_name": "AI Systems Ltd",
            "email": "info@aisystems.com",
            "website": "https://aisystems.com",
            "industry": "SaaS",
        },
    ]


# ============================================================================
# SUMMARY
# ============================================================================

if __name__ == "__main__":
    """
    Print configuration summary for debugging
    """
    print("\n" + "="*60)
    print("AI LEAD GENERATION - CONFIGURATION SUMMARY")
    print("="*60)
    
    print("\n📁 PROJECT PATHS:")
    print(f"  Project Root: {PROJECT_ROOT}")
    print(f"  Credentials: {CREDENTIALS_DIR}")
    print(f"  Data: {DATA_DIR}")
    print(f"  Logs: {LOGS_DIR}")
    print(f"  Output: {OUTPUT_DIR}")
    
    print("\n🔑 OPENROUTER API:")
    print(f"  API Key Set: {'✅ Yes' if OPENROUTER_API_KEY != 'not_set' else '❌ No'}")
    print(f"  Summary Model: {OPENROUTER_MODEL_SUMMARY}")
    print(f"  Email Model: {OPENROUTER_MODEL_EMAIL}")
    
    print("\n📊 GOOGLE SHEETS:")
    print(f"  Credentials File: {'✅ Exists' if GOOGLE_CREDENTIALS_FILE.exists() else '❌ Missing'}")
    print(f"  Sheet ID Set: {'✅ Yes' if GOOGLE_SHEET_ID != 'not_set' else '❌ No'}")
    print(f"  Sheet Name: {GOOGLE_SHEET_NAME}")
    
    print("\n⚙️  PROJECT SETTINGS:")
    print(f"  Max Leads per Batch: {MAX_LEADS_PER_BATCH}")
    print(f"  Website Timeout: {WEBSITE_TIMEOUT_SECONDS}s")
    print(f"  Max Content Length: {MAX_WEBSITE_CONTENT_LENGTH} chars")
    print(f"  Log Level: {LOG_LEVEL}")
    print(f"  Debug Mode: {DEBUG_MODE}")
    
    print("\n" + "="*60)
    print("Validating configuration...")
    print("="*60)
    
    try:
        validate_configuration()
        print("✅ All critical configurations validated successfully!")
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
    
    print("\n" + "="*60 + "\n")