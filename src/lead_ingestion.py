"""
lead_ingestion.py - Lead Data Ingestion
=======================================
Read lead data from:
1. CSV files
2. Google Sheets
3. Manual input (for testing)

Validates and cleans data before processing.
"""

import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials

from .config import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_SHEET_ID,
    GOOGLE_SHEET_NAME,
    GOOGLE_SHEETS_SCOPES,
    get_sample_leads_data,
)
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    DataValidationError,
    GoogleSheetsError,
)

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class LeadIngestion:
    """
    Handle lead data ingestion from various sources
    """
    
    def __init__(self):
        """Initialize lead ingestion"""
        self.logger = logger
        self.error_tracker = error_tracker
        self.leads = []
    
    # ========================================================================
    # CSV READING
    # ========================================================================
    
    def read_from_csv(self, file_path: str) -> List[Dict]:
        """
        Read leads from CSV file
        
        Args:
            file_path (str): Path to CSV file
        
        Returns:
            List[Dict]: List of lead dictionaries
        
        Expected CSV columns:
            - company_name (required)
            - email (optional)
            - website (optional)
            - industry (optional)
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            self.logger.info(f"Reading leads from CSV: {file_path}")
            
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Validate required columns
            if 'company_name' not in df.columns:
                raise DataValidationError(
                    "CSV must contain 'company_name' column"
                )
            
            # Convert to list of dictionaries
            leads = df.to_dict('records')
            
            # Clean and validate each lead
            cleaned_leads = []
            for lead in leads:
                cleaned = self._clean_lead(lead)
                if cleaned:
                    cleaned_leads.append(cleaned)
            
            self.logger.info(
                f"✅ Read {len(cleaned_leads)} valid leads from CSV"
            )
            self.leads.extend(cleaned_leads)
            return cleaned_leads
        
        except FileNotFoundError as e:
            self.logger.error(f"❌ File not found: {e}")
            raise
        except DataValidationError as e:
            self.logger.error(f"❌ Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error reading CSV: {e}")
            raise
    
    # ========================================================================
    # GOOGLE SHEETS READING
    # ========================================================================
    
    def read_from_google_sheets(self) -> List[Dict]:
        """
        Read leads from Google Sheets
        
        Returns:
            List[Dict]: List of lead dictionaries
        
        Expected sheet columns:
            - Company Name (required)
            - Email (optional)
            - Website (optional)
            - Industry (optional)
        """
        try:
            self.logger.info(
                f"Reading leads from Google Sheets: {GOOGLE_SHEET_ID}"
            )
            
            # Authenticate
            creds = Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_PATH,
                scopes=GOOGLE_SHEETS_SCOPES
            )
            
            client = gspread.authorize(creds)
            
            # Open spreadsheet
            spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
            worksheet = spreadsheet.worksheet(GOOGLE_SHEET_NAME)
            
            # Get all values
            all_values = worksheet.get_all_values()
            
            if not all_values or len(all_values) < 2:
                self.logger.warning("No data in Google Sheet")
                return []
            
            # Parse header and data
            headers = all_values[0]
            data = all_values[1:]
            
            # Convert to dictionaries
            leads = []
            for row in data:
                lead = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        lead[header.lower().strip()] = row[i]
                    else:
                        lead[header.lower().strip()] = ""
                leads.append(lead)
            
            # Clean and validate
            cleaned_leads = []
            for lead in leads:
                # Normalize keys
                normalized = {
                    'company_name': lead.get('company name', ''),
                    'email': lead.get('email', ''),
                    'website': lead.get('website', ''),
                    'industry': lead.get('industry', ''),
                }
                cleaned = self._clean_lead(normalized)
                if cleaned:
                    cleaned_leads.append(cleaned)
            
            self.logger.info(
                f"✅ Read {len(cleaned_leads)} valid leads from Google Sheets"
            )
            self.leads.extend(cleaned_leads)
            return cleaned_leads
        
        except GoogleSheetsError as e:
            self.logger.error(f"❌ Google Sheets error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error reading Google Sheets: {e}")
            raise GoogleSheetsError(str(e))
    
    # ========================================================================
    # MANUAL INPUT (FOR TESTING)
    # ========================================================================
    
    def read_sample_leads(self) -> List[Dict]:
        """
        Read sample leads (for testing)
        
        Returns:
            List[Dict]: List of sample lead dictionaries
        """
        try:
            self.logger.info("Reading sample leads for testing")
            
            sample_leads = get_sample_leads_data()
            
            cleaned_leads = []
            for lead in sample_leads:
                cleaned = self._clean_lead(lead)
                if cleaned:
                    cleaned_leads.append(cleaned)
            
            self.logger.info(f"✅ Loaded {len(cleaned_leads)} sample leads")
            self.leads.extend(cleaned_leads)
            return cleaned_leads
        
        except Exception as e:
            self.logger.error(f"❌ Error loading sample leads: {e}")
            raise
    
    # ========================================================================
    # DATA CLEANING & VALIDATION
    # ========================================================================
    
    def _clean_lead(self, lead: Dict) -> Optional[Dict]:
        """
        Clean and validate a single lead
        
        Args:
            lead (Dict): Raw lead data
        
        Returns:
            Dict or None: Cleaned lead, or None if invalid
        """
        try:
            # Extract fields
            company_name = str(lead.get('company_name', '')).strip()
            email = str(lead.get('email', '')).strip()
            website = str(lead.get('website', '')).strip()
            industry = str(lead.get('industry', '')).strip()
            
            # Company name is required
            if not company_name:
                self.logger.debug("Skipping: No company name")
                return None
            
            # At least one contact info required
            if not email and not website:
                self.logger.debug(
                    f"Skipping '{company_name}': No email or website"
                )
                return None
            
            # Validate email format if provided
            if email and not self._is_valid_email(email):
                self.logger.debug(
                    f"Skipping '{company_name}': Invalid email format"
                )
                return None
            
            # Validate URL format if provided
            if website and not self._is_valid_url(website):
                self.logger.debug(
                    f"Skipping '{company_name}': Invalid website URL"
                )
                return None
            
            # Return cleaned lead
            return {
                'company_name': company_name,
                'email': email,
                'website': website,
                'industry': industry,
            }
        
        except Exception as e:
            self.logger.debug(f"Error cleaning lead: {e}")
            return None
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        return '@' in email and '.' in email.split('@')[-1]
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False
        url_lower = url.lower()
        return (url_lower.startswith('http://') or 
                url_lower.startswith('https://') or
                url_lower.startswith('www.') or
                '.' in url)
    
    # ========================================================================
    # DUPLICATE DETECTION
    # ========================================================================
    
    def remove_duplicates(self) -> List[Dict]:
        """
        Remove duplicate leads based on company name and email
        
        Returns:
            List[Dict]: Deduplicated leads
        """
        seen = set()
        unique_leads = []
        
        for lead in self.leads:
            # Create unique key
            key = (
                lead['company_name'].lower(),
                lead['email'].lower() if lead['email'] else ''
            )
            
            if key not in seen:
                seen.add(key)
                unique_leads.append(lead)
            else:
                self.logger.debug(
                    f"Removing duplicate: {lead['company_name']}"
                )
        
        removed_count = len(self.leads) - len(unique_leads)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} duplicate leads")
        
        self.leads = unique_leads
        return unique_leads
    
    # ========================================================================
    # DATA RETRIEVAL
    # ========================================================================
    
    def get_all_leads(self) -> List[Dict]:
        """Get all loaded leads"""
        return self.leads
    
    def get_leads_count(self) -> int:
        """Get total number of leads"""
        return len(self.leads)
    
    def get_leads_by_industry(self, industry: str) -> List[Dict]:
        """Get leads filtered by industry"""
        return [
            lead for lead in self.leads
            if lead['industry'].lower() == industry.lower()
        ]
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    def export_to_csv(self, file_path: str) -> bool:
        """
        Export leads to CSV file
        
        Args:
            file_path (str): Path to export CSV
        
        Returns:
            bool: True if successful
        """
        try:
            df = pd.DataFrame(self.leads)
            df.to_csv(file_path, index=False)
            self.logger.info(f"✅ Exported {len(self.leads)} leads to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error exporting to CSV: {e}")
            return False


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test lead ingestion
    """
    print("\n" + "="*60)
    print("TESTING LEAD INGESTION")
    print("="*60 + "\n")
    
    ingestion = LeadIngestion()
    
    # Test 1: Load sample leads
    print("Test 1: Loading sample leads...")
    sample = ingestion.read_from_csv("data/sample_leads.csv")
    print(f"✅ Loaded {len(sample)} sample leads")
    
    # Display sample leads
    print("\nSample Leads:")
    for lead in sample:
        print(f"  - {lead['company_name']}")
        print(f"    Email: {lead['email']}")
        print(f"    Website: {lead['website']}")
        print(f"    Industry: {lead['industry']}\n")
    
    # Test 2: Remove duplicates
    print("\nTest 2: Removing duplicates...")
    ingestion.leads.append(sample[0])  # Add duplicate
    ingestion.remove_duplicates()
    print(f"✅ Leads after dedup: {ingestion.get_leads_count()}")
    
    # Test 3: Export
    print("\nTest 3: Exporting to CSV...")
    ingestion.export_to_csv("data/sample_leads.csv")
    
    print("\n" + "="*60)
    print("✅ Lead ingestion test completed!")
    print("="*60 + "\n")