"""
sheets_integration.py - Google Sheets Integration
==================================================
Read and write lead data to Google Sheets using:
- Google Sheets API
- gspread library
- Service Account authentication

Handles:
- Reading leads from sheets
- Writing results back to sheets
- Creating new sheets if needed
- Updating individual cells/rows
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from datetime import datetime

from .config import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_SHEET_ID,
    GOOGLE_SHEET_NAME,
    GOOGLE_SHEETS_SCOPES,
)
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    GoogleSheetsError,
)

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class SheetsIntegration:
    """
    Handle Google Sheets operations for lead data
    """
    
    def __init__(self):
        """Initialize Google Sheets integration"""
        self.logger = logger
        self.error_tracker = error_tracker
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        
        self._authenticate()
    
    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    
    def _authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API
        
        Returns:
            bool: True if successful
        """
        try:
            self.logger.info("Authenticating with Google Sheets API...")
            
            # Load credentials
            creds = Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_PATH,
                scopes=GOOGLE_SHEETS_SCOPES
            )
            
            # Create client
            self.client = gspread.authorize(creds)
            
            self.logger.info("✅ Google Sheets authentication successful!")
            return True
        
        except FileNotFoundError:
            error_msg = (
                f"Credentials file not found: {GOOGLE_CREDENTIALS_PATH}"
            )
            self.logger.error(f"❌ {error_msg}")
            raise GoogleSheetsError(error_msg)
        
        except Exception as e:
            error_msg = f"Authentication failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise GoogleSheetsError(error_msg)
    
    # ========================================================================
    # SHEET OPERATIONS
    # ========================================================================
    
    def get_worksheet(self, sheet_name: str = None) -> bool:
        """
        Open and get worksheet
        
        Args:
            sheet_name (str): Worksheet name (default: from config)
        
        Returns:
            bool: True if successful
        """
        try:
            sheet_name = sheet_name or GOOGLE_SHEET_NAME
            
            self.logger.info(
                f"Opening spreadsheet: {GOOGLE_SHEET_ID}"
            )
            
            # Open spreadsheet
            self.spreadsheet = self.client.open_by_key(GOOGLE_SHEET_ID)
            
            self.logger.info(f"Opening worksheet: {sheet_name}")
            
            # Get or create worksheet
            try:
                self.worksheet = self.spreadsheet.worksheet(sheet_name)
                self.logger.info(f"✅ Worksheet '{sheet_name}' opened")
            except gspread.exceptions.WorksheetNotFound:
                self.logger.warning(
                    f"Worksheet '{sheet_name}' not found. Creating..."
                )
                self.worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=20
                )
                self.logger.info(f"✅ Worksheet '{sheet_name}' created")
            
            return True
        
        except Exception as e:
            error_msg = f"Failed to open worksheet: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise GoogleSheetsError(error_msg)
    
    # ========================================================================
    # READING DATA
    # ========================================================================
    
    def read_leads(self) -> List[Dict]:
        """
        Read all leads from worksheet
        
        Returns:
            List[Dict]: List of lead dictionaries
        """
        try:
            if not self.worksheet:
                self.get_worksheet()
            
            self.logger.info("Reading leads from Google Sheets...")
            
            # Get all values
            all_values = self.worksheet.get_all_values()
            
            if not all_values or len(all_values) < 2:
                self.logger.warning("No data in worksheet")
                return []
            
            # Parse header and data
            headers = all_values[0]
            data = all_values[1:]
            
            # Convert to dictionaries
            leads = []
            for row_idx, row in enumerate(data, 2):  # Start from row 2
                lead = {}
                for col_idx, header in enumerate(headers):
                    if col_idx < len(row):
                        lead[header.lower().strip()] = row[col_idx]
                    else:
                        lead[header.lower().strip()] = ""
                
                # Add row number for updating later
                lead['_row_number'] = row_idx
                leads.append(lead)
            
            self.logger.info(f"✅ Read {len(leads)} leads from Google Sheets")
            return leads
        
        except Exception as e:
            error_msg = f"Failed to read leads: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise GoogleSheetsError(error_msg)
    
    # ========================================================================
    # WRITING DATA
    # ========================================================================
    
    def initialize_sheet(self, headers: List[str]) -> bool:
        """
        Initialize sheet with headers
        
        Args:
            headers (List[str]): Column headers
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.worksheet:
                self.get_worksheet()
            
            self.logger.info("Initializing sheet with headers...")
            
            # Clear existing data
            self.worksheet.clear()
            
            # Write headers
            self.worksheet.insert_row(headers, index=1)
            
            self.logger.info(f"✅ Sheet initialized with {len(headers)} columns")
            return True
        
        except Exception as e:
            error_msg = f"Failed to initialize sheet: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise GoogleSheetsError(error_msg)
    
    def write_leads(self, leads: List[Dict]) -> bool:
        """
        Write leads to worksheet using a SINGLE batch request.

        Uses worksheet.update() instead of repeated append_row() calls to
        avoid Google Sheets API rate limits (60 req/min on free tier).

        Args:
            leads (List[Dict]): List of lead dictionaries

        Returns:
            bool: True if successful
        """
        try:
            if not self.worksheet:
                self.get_worksheet()

            if not leads:
                self.logger.warning("No leads to write")
                return False

            self.logger.info(f"Writing {len(leads)} leads to Google Sheets (batch)...")

            # Get headers (excluding internal _ fields)
            headers = [
                h for h in leads[0].keys() if not h.startswith('_')
            ]

            # Build all rows as a 2D list
            rows = [
                [str(lead.get(h, '')) for h in headers]
                for lead in leads
            ]

            # Clear and write in ONE API call (headers + data)
            self.worksheet.clear()
            self.worksheet.update('A1', [headers] + rows)

            self.logger.info(f"Wrote {len(leads)} leads to Google Sheets")
            return True

        except Exception as e:
            error_msg = f"Failed to write leads: {str(e)}"
            self.logger.error(f"{error_msg}")
            raise GoogleSheetsError(error_msg)

    def write_leads_batch(
        self,
        leads: List[Dict],
        headers: List[str],
        truncate_fields: dict = None,
    ) -> bool:
        """
        Write processed leads to the worksheet in a single batch API call.

        This is the primary method used by the pipeline's Phase 6.
        Replaces the old per-row append_row() loop which hit rate limits.

        Args:
            leads (List[Dict]):        Processed lead records
            headers (List[str]):       Column names (in desired order)
            truncate_fields (dict):    Optional {field_name: max_chars} truncation map

        Returns:
            bool: True if successful
        """
        try:
            if not self.worksheet:
                self.get_worksheet()

            if not leads:
                self.logger.warning("No leads to write (batch)")
                return False

            truncate_fields = truncate_fields or {}

            self.logger.info(
                f"Batch-writing {len(leads)} leads with "
                f"{len(headers)} columns..."
            )

            # Build rows
            rows = []
            for lead in leads:
                row = []
                for field in headers:
                    value = str(lead.get(field, ''))
                    max_len = truncate_fields.get(field)
                    if max_len and len(value) > max_len:
                        value = value[:max_len]
                    row.append(value)
                rows.append(row)

            # Single API call: clear + write headers + all data
            self.worksheet.clear()
            self.worksheet.update('A1', [headers] + rows)

            self.logger.info(
                f"Updated {len(leads)} rows in Google Sheets (1 API call)"
            )
            sheet_url = self.get_sheet_url()
            self.logger.info(f"View results: {sheet_url}")
            return True

        except Exception as e:
            error_msg = f"Failed to batch-write leads: {str(e)}"
            self.logger.error(f"{error_msg}")
            raise GoogleSheetsError(error_msg)
    
    def update_lead(self, row_number: int, data: Dict) -> bool:
        """
        Update a single lead row
        
        Args:
            row_number (int): Row number to update
            data (Dict): Data to update
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.worksheet:
                self.get_worksheet()
            
            self.logger.debug(f"Updating row {row_number}...")
            
            # Get headers
            headers = self.worksheet.row_values(1)
            
            # Update each field
            for col_idx, header in enumerate(headers, 1):
                if header.lower() in data:
                    value = str(data[header.lower()])
                    self.worksheet.update_cell(row_number, col_idx, value)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to update row {row_number}: {str(e)}")
            return False
    
    def append_result_columns(self) -> bool:
        """
        Add result columns if they don't exist
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.worksheet:
                self.get_worksheet()
            
            headers = self.worksheet.row_values(1)
            headers_lower = [h.lower() for h in headers]
            
            # Define result columns
            result_columns = [
                'Extracted Domain',
                'Website Summary',
                'Generated Email',
                'Processing Status',
                'Processed Date',
            ]
            
            # Add missing columns
            for col_name in result_columns:
                if col_name.lower() not in headers_lower:
                    headers.append(col_name)
                    self.logger.debug(f"Added column: {col_name}")
            
            # Update header row if new columns were added
            if len(headers) > len(self.worksheet.row_values(1)):
                self.worksheet.delete_rows(1)
                self.worksheet.insert_row(headers, index=1)
                self.logger.info("✅ Result columns added")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to append result columns: {str(e)}")
            return False
    
    # ========================================================================
    # BATCH UPDATES
    # ========================================================================
    
    def write_processing_results(self, results: List[Dict]) -> bool:
        """
        Write processing results back to sheet
        
        Args:
            results (List[Dict]): List of processed lead results
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.worksheet:
                self.get_worksheet()
            
            self.logger.info(f"Writing results for {len(results)} leads...")
            
            # Get current headers
            headers = self.worksheet.row_values(1)
            headers_lower = [h.lower() for h in headers]
            
            # Ensure result columns exist
            result_col_map = {}
            for i, header in enumerate(headers_lower, 1):
                if 'domain' in header:
                    result_col_map['domain'] = i
                elif 'summary' in header:
                    result_col_map['summary'] = i
                elif 'email' in header:
                    result_col_map['email'] = i
                elif 'status' in header:
                    result_col_map['status'] = i
                elif 'date' in header:
                    result_col_map['date'] = i
            
            # Update each row
            for result in results:
                row_num = result.get('_row_number')
                
                if not row_num:
                    continue
                
                # Extract domain
                if 'domain' in result_col_map and result.get('extracted_domain'):
                    self.worksheet.update_cell(
                        row_num,
                        result_col_map['domain'],
                        result['extracted_domain']
                    )
                
                # Website summary
                if 'summary' in result_col_map and result.get('business_summary'):
                    self.worksheet.update_cell(
                        row_num,
                        result_col_map['summary'],
                        result['business_summary'][:200]  # Limit length
                    )
                
                # Generated email
                if 'email' in result_col_map and result.get('generated_email'):
                    email_preview = result['generated_email'][:100]
                    self.worksheet.update_cell(
                        row_num,
                        result_col_map['email'],
                        email_preview
                    )
                
                # Status
                if 'status' in result_col_map:
                    status = result.get('email_status', 'pending')
                    self.worksheet.update_cell(
                        row_num,
                        result_col_map['status'],
                        status
                    )
                
                # Date
                if 'date' in result_col_map:
                    self.worksheet.update_cell(
                        row_num,
                        result_col_map['date'],
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
            
            self.logger.info(f"✅ Updated {len(results)} rows in Google Sheets")
            return True
        
        except Exception as e:
            error_msg = f"Failed to write results: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise GoogleSheetsError(error_msg)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_sheet_url(self) -> str:
        """
        Get URL to the Google Sheet
        
        Returns:
            str: Sheet URL
        """
        return f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit"
    
    def get_row_count(self) -> int:
        """
        Get number of rows in worksheet
        
        Returns:
            int: Row count
        """
        try:
            if not self.worksheet:
                self.get_worksheet()
            return len(self.worksheet.get_all_values())
        except:
            return 0
    
    def clear_sheet(self) -> bool:
        """
        Clear all data from worksheet
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.worksheet:
                self.get_worksheet()
            
            self.worksheet.clear()
            self.logger.info("✅ Worksheet cleared")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear worksheet: {e}")
            return False


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test Google Sheets integration
    """
    print("\n" + "="*60)
    print("TESTING GOOGLE SHEETS INTEGRATION")
    print("="*60 + "\n")
    
    try:
        sheets = SheetsIntegration()
        
        # Test 1: Get worksheet
        print("Test 1: Opening worksheet...")
        sheets.get_worksheet()
        print(f"✅ Worksheet opened")
        print(f"   Current rows: {sheets.get_row_count()}")
        
        # Test 2: Read leads
        print("\nTest 2: Reading leads from sheet...")
        leads = sheets.read_leads()
        print(f"✅ Read {len(leads)} leads")
        
        if leads:
            print("\n   Sample lead:")
            for key, value in list(leads[0].items())[:5]:
                print(f"   - {key}: {value}")
        
        # Test 3: Sheet URL
        print("\nTest 3: Sheet information")
        print(f"✅ Sheet URL: {sheets.get_sheet_url()}")
        
        print("\n" + "="*60)
        print("✅ Google Sheets integration test completed!")
        print("="*60 + "\n")
    
    except GoogleSheetsError as e:
        print(f"❌ Google Sheets error: {e}")
        print("\n   Make sure:")
        print("   1. google_credentials.json exists in credentials/")
        print("   2. Service account has editor access to the sheet")
        print("   3. GOOGLE_SHEET_ID is correct in .env")