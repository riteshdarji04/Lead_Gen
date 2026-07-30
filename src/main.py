# """
# main.py - Main Orchestration Script
# ====================================
# Complete pipeline orchestration:
# 1. Read leads (CSV or Google Sheets)
# 2. Extract domains
# 3. Scrape websites
# 4. Generate AI summaries
# 5. Generate personalized emails
# 6. Write results to Google Sheets

# Run the complete lead generation workflow end-to-end.
# """

# import sys
# import time
# from pathlib import Path
# from typing import List, Dict

# from .config import (
#     validate_configuration,
#     MAX_LEADS_PER_BATCH,
#     SAMPLE_CSV,
# )
# from .error_handler import (
#     LoggerSetup,
#     ErrorTracker,
#     log_section,
#     log_progress,
# )
# from .lead_ingestion import LeadIngestion
# from .lead_discovery import LeadDiscovery
# from .domain_extraction import DomainExtractor
# from .website_scraper import WebsiteScraper
# from .ai_summarizer import AISummarizer
# from .email_generator import EmailGenerator
# from .sheets_integration import SheetsIntegration

# # Setup logger
# logger = LoggerSetup.get_logger(__name__)
# error_tracker = ErrorTracker()


# class LeadGenerationPipeline:
#     """
#     Main orchestration class for the complete pipeline
#     """
    
#     def __init__(self):
#         """Initialize pipeline"""
#         self.logger = logger
#         self.error_tracker = error_tracker

#         # Initialize modules
#         self.ingestion = LeadIngestion()
#         self.discovery = LeadDiscovery()   # Scenario 2
#         self.extractor = DomainExtractor()
#         self.scraper = WebsiteScraper()
#         self.summarizer = AISummarizer()
#         self.email_gen = EmailGenerator()
#         self.sheets = SheetsIntegration()

#         # Pipeline state
#         self.leads = []
#         self.processed_leads = []
#         self.start_time = None
    
#     # ========================================================================
#     # MAIN PIPELINE EXECUTION
#     # ========================================================================
    
#     def run_pipeline(
#         self,
#         source: str = 'csv',
#         csv_path: str = None,
#         max_leads: int = None,
#         update_sheets: bool = True
#     ) -> Dict:
#         """
#         Run the complete pipeline.
#         """
#         try:
#             self.start_time = time.time()

#             # Validate configuration
#             log_section("VALIDATING CONFIGURATION", "INFO")
#             validate_configuration()
#             print("Configuration validated\n")

#             # Phase 1: Lead Ingestion
#             log_section("PHASE 1: LEAD INGESTION", "INFO")
#             self.leads = self._run_ingestion(source, csv_path)

#             if not self.leads:
#                 self.logger.error("No leads to process!")
#                 return self._get_results()

#             if max_leads and max_leads > 0:
#                 self.leads = self.leads[:max_leads]
#                 self.logger.info(f"Limited processing to {len(self.leads)} leads (--max-leads)")

#             print(f"Loaded {len(self.leads)} leads\n")

#             # Phase 2: Domain Extraction
#             log_section("PHASE 2: DOMAIN EXTRACTION", "INFO")
#             self.leads = self._run_domain_extraction()
#             print()

#             # Phase 3: Website Scraping
#             log_section("PHASE 3: WEBSITE SCRAPING", "INFO")
#             self.leads = self._run_website_scraping()
#             print()

#             # Phase 4: AI Summarization
#             log_section("PHASE 4: AI SUMMARIZATION", "INFO")
#             self.leads = self._run_summarization()
#             print()

#             # Phase 5: Email Generation
#             log_section("PHASE 5: EMAIL GENERATION", "INFO")
#             self.leads = self._run_email_generation()
#             print()

#             # Phase 6: Google Sheets Integration
#             if update_sheets:
#                 log_section("PHASE 6: GOOGLE SHEETS UPDATE", "INFO")
#                 self._run_sheets_integration()
#                 print()

#             # Final Summary
#             log_section("PIPELINE COMPLETE", "INFO")
#             results = self._get_results()
#             self._print_summary(results)

#             return results

#         except Exception as e:
#             self.logger.error(f"Pipeline failed: {e}")
#             return self._get_results()

#     def run_pipeline_scenario2(
#         self,
#         industry: str,
#         topic: str = None,
#         location: str = None,
#         num_results: int = 50,
#         update_sheets: bool = True
#     ) -> Dict:
#         """
#         Run pipeline for Scenario 2: Auto-discover companies
#         """
#         try:
#             self.start_time = time.time()
            
#             # Validate config
#             log_section("VALIDATING CONFIGURATION", "INFO")
#             validate_configuration()
#             print("Configuration validated\n")
            
#             # PHASE 0: Company Discovery
#             log_section("PHASE 0: COMPANY DISCOVERY", "INFO")
#             from .company_discovery import CompanyDiscovery
            
#             discoverer = CompanyDiscovery()
#             discovered_companies = discoverer.discover_companies(
#                 industry=industry,
#                 topic=topic,
#                 location=location,
#                 num_results=num_results
#             )
            
#             if not discovered_companies:
#                 self.logger.error("No companies discovered!")
#                 return self._get_results()
            
#             # Convert discovered companies to lead format
#             self.leads = [
#                 {
#                     'company_name': c.get('company_name', ''),
#                     'email': c.get('email', ''),
#                     'website': c.get('website', ''),
#                     'industry': c.get('industry', industry),
#                     'source': 'discovery',
#                 }
#                 for c in discovered_companies
#             ]
            
#             print(f"✅ Discovered {len(self.leads)} companies\n")
            
#             # Run all phases (Domain extraction -> Scraping -> Summarization -> Email)
#             log_section("PHASE 1: DOMAIN EXTRACTION", "INFO")
#             self.leads = self._run_domain_extraction()
#             print()

#             log_section("PHASE 2: WEBSITE SCRAPING", "INFO")
#             self.leads = self._run_website_scraping()
#             print()

#             log_section("PHASE 3: AI SUMMARIZATION", "INFO")
#             self.leads = self._run_summarization()
#             print()

#             log_section("PHASE 4: EMAIL GENERATION", "INFO")
#             self.leads = self._run_email_generation()
#             print()
            
#             # Phase 5: Google Sheets (APPEND mode)
#             if update_sheets:
#                 log_section("PHASE 5: GOOGLE SHEETS UPDATE", "INFO")
#                 self._run_sheets_integration()
#                 print()
            
#             # Final summary
#             log_section("PIPELINE COMPLETE", "INFO")
#             results = self._get_results()
#             self._print_summary(results)
            
#             return results
        
#         except Exception as e:
#             self.logger.error(f"Pipeline failed: {e}")
#             return self._get_results()
    
#     # ========================================================================
#     # PHASE 1: LEAD INGESTION
#     # ========================================================================
    
#     def _run_ingestion(self, source: str, csv_path: str = None) -> List[Dict]:
#         """Run lead ingestion phase (Scenario 1)."""
#         try:
#             if source == 'csv':
#                 if csv_path:
#                     path_to_use = csv_path
#                 elif SAMPLE_CSV.exists():
#                     path_to_use = str(SAMPLE_CSV)
#                     self.logger.info(
#                         f"No --csv path given; using default: {path_to_use}"
#                     )
#                 else:
#                     raise ValueError(
#                         "CSV path required: pass --csv <path> or place your "
#                         "data at data/sample_leads.csv"
#                     )

#                 self.logger.info(f"Reading from CSV: {path_to_use}")
#                 leads = self.ingestion.read_from_csv(path_to_use)

#             elif source == 'google_sheets':
#                 self.logger.info("Reading from Google Sheets")
#                 leads = self.sheets.read_leads()

#             else:
#                 raise ValueError(f"Unknown source: {source}")

#             if not leads:
#                 self.logger.error("No leads loaded!")
#                 return []

#             # Remove duplicates
#             self.ingestion.leads = leads
#             leads = self.ingestion.remove_duplicates()

#             self.logger.info(f"Ingestion complete: {len(leads)} leads")
#             return leads

#         except Exception as e:
#             self.logger.error(f"Ingestion failed: {e}")
#             raise
    
#     # ========================================================================
#     # PHASE 2: DOMAIN EXTRACTION
#     # ========================================================================
    
#     def _run_domain_extraction(self) -> List[Dict]:
#         """Run domain extraction phase"""
#         try:
#             results = self.extractor.extract_domains_batch(self.leads)
            
#             # Count results
#             successful = sum(
#                 1 for r in results if r.get('extracted_domain')
#             )
#             failed = len(results) - successful
            
#             self.logger.info(
#                 f"✅ Domain extraction: {successful} success, {failed} failed"
#             )
#             return results
        
#         except Exception as e:
#             self.logger.error(f"❌ Domain extraction failed: {e}")
#             raise
    
#     # ========================================================================
#     # PHASE 3: WEBSITE SCRAPING
#     # ========================================================================
    
#     def _run_website_scraping(self) -> List[Dict]:
#         """Run website scraping phase"""
#         try:
#             results = self.scraper.scrape_websites_batch(self.leads)
            
#             # Count results
#             successful = sum(
#                 1 for r in results if r.get('scrape_status') == 'success'
#             )
#             failed = sum(
#                 1 for r in results if r.get('scrape_status') == 'failed'
#             )
            
#             self.logger.info(
#                 f"✅ Website scraping: {successful} success, {failed} failed"
#             )
#             return results
        
#         except Exception as e:
#             self.logger.error(f"❌ Website scraping failed: {e}")
#             raise
    
#     # ========================================================================
#     # PHASE 4: AI SUMMARIZATION
#     # ========================================================================
    
#     def _run_summarization(self) -> List[Dict]:
#         """Run AI summarization phase"""
#         try:
#             results = self.summarizer.summarize_batch(self.leads)
            
#             # Count results
#             successful = sum(
#                 1 for r in results if r.get('summary_status') == 'success'
#             )
#             failed = sum(
#                 1 for r in results if r.get('summary_status') == 'failed'
#             )
#             skipped = sum(
#                 1 for r in results if r.get('summary_status') == 'skipped'
#             )
            
#             self.logger.info(
#                 f"✅ Summarization: {successful} success, "
#                 f"{failed} failed, {skipped} skipped"
#             )
#             return results
        
#         except Exception as e:
#             self.logger.error(f"❌ Summarization failed: {e}")
#             raise
    
#     # ========================================================================
#     # PHASE 5: EMAIL GENERATION
#     # ========================================================================
    
#     def _run_email_generation(self) -> List[Dict]:
#         """Run email generation phase"""
#         try:
#             results = self.email_gen.generate_emails_batch(self.leads)
            
#             # Count results
#             successful = sum(
#                 1 for r in results if r.get('email_status') == 'success'
#             )
#             failed = sum(
#                 1 for r in results if r.get('email_status') == 'failed'
#             )
#             skipped = sum(
#                 1 for r in results if r.get('email_status') == 'skipped'
#             )
            
#             self.logger.info(
#                 f"✅ Email generation: {successful} success, "
#                 f"{failed} failed, {skipped} skipped"
#             )
#             return results
        
#         except Exception as e:
#             self.logger.error(f"❌ Email generation failed: {e}")
#             raise
    
#     # ========================================================================
#     # PHASE 6: GOOGLE SHEETS INTEGRATION
#     # ========================================================================
    
#     def _run_sheets_integration(self) -> bool:
#         """Run Google Sheets integration phase (APPEND mode - preserving old values)"""
#         try:
#             # Get worksheet
#             self.sheets.get_worksheet()
            
#             # DON'T CLEAR - Check if headers exist
#             current_rows = self.sheets.worksheet.get_all_values()
            
#             if not current_rows:
#                 # First time - add headers
#                 headers = [
#                     'company_name',
#                     'email',
#                     'website',
#                     'industry',
#                     'extracted_domain',
#                     'website_content',
#                     'business_summary',
#                     'generated_email',
#                     'email_status',
#                     'processed_date'
#                 ]
#                 self.sheets.initialize_sheet(headers)
#                 self.logger.info("✅ Headers added to empty sheet")
            
#             # Helper to convert HTML to simple plain text if needed
#             import re
#             def clean_html(text):
#                 if not text:
#                     return ''
#                 clean = re.sub('<[^<]+?>', '', str(text))
#                 return clean.strip()

#             # APPEND new data (don't clear old)
#             for lead in self.leads:
#                 email_content = clean_html(lead.get('generated_email', ''))
#                 row_data = [
#                     lead.get('company_name', ''),
#                     lead.get('email', ''),
#                     lead.get('website', ''),
#                     lead.get('industry', ''),
#                     lead.get('extracted_domain', ''),
#                     lead.get('website_content', ''),
#                     lead.get('business_summary', ''),
#                     email_content,
#                     lead.get('email_status', 'pending'),
#                     time.strftime('%Y-%m-%d %H:%M:%S'),
#                 ]
#                 self.sheets.worksheet.append_row(row_data)
            
#             self.logger.info(
#                 f"✅ Appended {len(self.leads)} new rows to Google Sheets (old data preserved)"
#             )
#             self.logger.info(
#                 f"📊 View results: {self.sheets.get_sheet_url()}"
#             )
#             return True
        
#         except Exception as e:
#             error_msg = f"Failed to append to sheets: {str(e)}"
#             self.logger.error(f"❌ {error_msg}")
#             return False
    
#     # ========================================================================
#     # RESULTS & REPORTING
#     # ========================================================================
    
#     def _get_results(self) -> Dict:
#         """Get pipeline results"""
#         elapsed_time = (
#             time.time() - self.start_time if self.start_time else 0
#         )
        
#         return {
#             'total_leads': len(self.leads),
#             'processed_leads': len(
#                 [l for l in self.leads if l.get('email_status') == 'success']
#             ),
#             'elapsed_time': elapsed_time,
#             'errors': error_tracker.get_error_summary(),
#             'leads': self.leads,
#         }
    
#     def _print_summary(self, results: Dict):
#         """Print final summary"""
#         print("\n" + "="*70)
#         print("FINAL SUMMARY")
#         print("="*70)
        
#         print(f"\n📊 STATISTICS:")
#         print(f"  Total Leads: {results['total_leads']}")
#         print(f"  Successfully Processed: {results['processed_leads']}")
#         print(f"  Success Rate: {(results['processed_leads']/max(results['total_leads'],1)*100):.1f}%")
#         print(f"  Time Elapsed: {results['elapsed_time']:.2f} seconds")
        
#         if results['errors']:
#             print(f"\n⚠️  Errors: {results['errors']['total_errors']}")
#             print(f"  By Type:")
#             for error_type, count in results['errors']['errors_by_type'].items():
#                 print(f"    - {error_type}: {count}")
        
#         print("\n" + "="*70)
#         print("✅ PIPELINE COMPLETE!")
#         print("="*70 + "\n")


# # ============================================================================
# # COMMAND LINE INTERFACE
# # ============================================================================

# def main():
#     """Main entry point"""
#     import argparse
    
#     parser = argparse.ArgumentParser(
#         description='AI Lead Generation Pipeline'
#     )
    
#     # Scenario selection
#     parser.add_argument(
#         '--scenario',
#         choices=['1', '2'],
#         default='1',
#         help='Scenario 1 (provided list) or 2 (auto-discover)'
#     )
    
#     # Scenario 1 args
#     parser.add_argument(
#         '--source',
#         choices=['google_sheets', 'csv'],
#         default='google_sheets',
#         help='Data source for Scenario 1'
#     )
#     parser.add_argument('--csv', type=str, help='CSV file path')
#     parser.add_argument('--max-leads', type=int, help='Maximum leads to process in Scenario 1')
    
#     # Scenario 2 args
#     parser.add_argument(
#         '--industry',
#         type=str,
#         help='Industry for Scenario 2 (e.g., "Healthcare AI")'
#     )
#     parser.add_argument(
#         '--topic',
#         type=str,
#         help='GitHub topic (e.g., "healthcare-ai")'
#     )
#     parser.add_argument(
#         '--location',
#         type=str,
#         help='Location filter'
#     )
#     parser.add_argument(
#         '--num-results',
#         type=int,
#         default=50,
#         help='Number of companies to find (Scenario 2)'
#     )
    
#     parser.add_argument(
#         '--no-sheets-update',
#         action='store_true',
#         help='Do not update Google Sheets'
#     )
    
#     args = parser.parse_args()
    
#     pipeline = LeadGenerationPipeline()
    
#     if args.scenario == '2':
#         # Scenario 2
#         results = pipeline.run_pipeline_scenario2(
#             industry=args.industry or "Technology",
#             topic=args.topic,
#             location=args.location,
#             num_results=args.num_results,
#             update_sheets=not args.no_sheets_update
#         )
#     else:
#         # Scenario 1
#         results = pipeline.run_pipeline(
#             source=args.source,
#             csv_path=args.csv,
#             max_leads=args.max_leads,
#             update_sheets=not args.no_sheets_update
#         )
    
#     sys.exit(0 if results['processed_leads'] > 0 else 1)



# # ============================================================================
# # EXAMPLE USAGE
# # ============================================================================

# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         main()
#     else:
#         print("\n" + "="*70)
#         print("AI LEAD GENERATION PIPELINE")
#         print("="*70 + "\n")

#         pipeline = LeadGenerationPipeline()

#         # Smart default: use sample CSV if it exists, else Google Sheets
#         if SAMPLE_CSV.exists():
#             print(f"  Auto-detected: using {SAMPLE_CSV}\n")
#             results = pipeline.run_pipeline(
#                 source='csv',
#                 csv_path=str(SAMPLE_CSV),
#                 update_sheets=True,
#             )
#         else:
#             print("  data/sample_leads.csv not found — reading from Google Sheets\n")
#             results = pipeline.run_pipeline(
#                 source='google_sheets',
#                 update_sheets=True,
#             )

#         print("\n" + "="*70)
#         print("Pipeline completed!")
#         print("="*70 + "\n")



































"""
main.py - Main Orchestration Script
====================================
Complete pipeline orchestration:
1. Read leads (CSV or Google Sheets)
2. Extract domains
3. Scrape websites
4. Generate AI summaries
5. Generate personalized emails
6. Write results to Google Sheets

Run the complete lead generation workflow end-to-end.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict

from .config import (
    validate_configuration,
    MAX_LEADS_PER_BATCH,
    SAMPLE_CSV,
)
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    log_section,
    log_progress,
)
from .lead_ingestion import LeadIngestion
from .lead_discovery import LeadDiscovery
from .domain_extraction import DomainExtractor
from .website_scraper import WebsiteScraper
from .ai_summarizer import AISummarizer
from .email_generator import EmailGenerator
from .sheets_integration import SheetsIntegration
from .results_exporter import ResultsExporter

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class LeadGenerationPipeline:
    """
    Main orchestration class for the complete pipeline
    """
    
    def __init__(self):
        """Initialize pipeline"""
        self.logger = logger
        self.error_tracker = error_tracker

        # Initialize modules
        self.ingestion = LeadIngestion()
        self.discovery = LeadDiscovery()   # Scenario 2
        self.extractor = DomainExtractor()
        self.scraper = WebsiteScraper()
        self.summarizer = AISummarizer()
        self.email_gen = EmailGenerator()
        self.sheets = SheetsIntegration()
        self.results_exporter = ResultsExporter()

        # State tracking
        self._current_scenario = "1"
        self._current_industry = ""

        # Validate Groq API Key on startup
        if not self.summarizer.validate_api_key():
            self.logger.warning("⚠️ Groq API key is missing or invalid. Check GROQ_API_KEY in your .env file.")

        # Pipeline state
        self.leads = []
        self.processed_leads = []
        self.start_time = None
    
    # ========================================================================
    # MAIN PIPELINE EXECUTION
    # ========================================================================
    
    def run_pipeline(
        self,
        source: str = 'csv',
        csv_path: str = None,
        max_leads: int = None,
        update_sheets: bool = True
    ) -> Dict:
        """
        Run the complete pipeline.
        """
        try:
            self.start_time = time.time()
            self._current_scenario = "1"
            self._current_industry = ""

            # Validate configuration
            log_section("VALIDATING CONFIGURATION", "INFO")
            validate_configuration()
            if not self.summarizer.validate_api_key():
                raise ValueError("GROQ_API_KEY is not configured or valid in .env")
            print("Configuration validated\n")

            # Phase 1: Lead Ingestion
            log_section("PHASE 1: LEAD INGESTION", "INFO")
            self.leads = self._run_ingestion(source, csv_path)

            if not self.leads:
                self.logger.error("No leads to process!")
                return self._get_results()

            if max_leads and max_leads > 0:
                self.leads = self.leads[:max_leads]
                self.logger.info(f"Limited processing to {len(self.leads)} leads (--max-leads)")

            print(f"Loaded {len(self.leads)} leads\n")

            # Phase 2: Domain Extraction
            log_section("PHASE 2: DOMAIN EXTRACTION", "INFO")
            self.leads = self._run_domain_extraction()
            print()

            # Phase 3: Website Scraping
            log_section("PHASE 3: WEBSITE SCRAPING", "INFO")
            self.leads = self._run_website_scraping()
            print()

            # Phase 4: AI Summarization
            log_section("PHASE 4: AI SUMMARIZATION", "INFO")
            self.leads = self._run_summarization()
            print()

            # Phase 5: Email Generation
            log_section("PHASE 5: EMAIL GENERATION", "INFO")
            self.leads = self._run_email_generation()
            print()

            # Phase 6: Google Sheets Integration
            if update_sheets:
                log_section("PHASE 6: GOOGLE SHEETS UPDATE", "INFO")
                self._run_sheets_integration()
                print()

            # Final Summary
            results = self._get_results()
            results = self._finalize_pipeline(results)

            return results

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return self._get_results()

    def run_pipeline_scenario2(
        self,
        industry: str,
        topic: str = None,
        location: str = None,
        num_results: int = 50,
        update_sheets: bool = True
    ) -> Dict:
        """
        Run pipeline for Scenario 2: Auto-discover companies
        """
        try:
            self.start_time = time.time()
            self._current_scenario = "2"
            self._current_industry = industry
            
            # Validate config
            log_section("VALIDATING CONFIGURATION", "INFO")
            validate_configuration()
            if not self.summarizer.validate_api_key():
                raise ValueError("GROQ_API_KEY is not configured or valid in .env")
            print("Configuration validated\n")
            
            # PHASE 0: Company Discovery
            log_section("PHASE 0: COMPANY DISCOVERY", "INFO")
            from .company_discovery import CompanyDiscovery
            
            discoverer = CompanyDiscovery()
            discovered_companies = discoverer.discover_companies(
                industry=industry,
                topic=topic,
                location=location,
                num_results=num_results
            )
            
            if not discovered_companies:
                self.logger.error("No companies discovered!")
                return self._get_results()
            
            # Convert discovered companies to lead format
            self.leads = [
                {
                    'company_name': c.get('company_name', ''),
                    'email': c.get('email', ''),
                    'website': c.get('website', ''),
                    'industry': c.get('industry', industry),
                    'source': 'discovery',
                }
                for c in discovered_companies
            ]
            
            print(f"✅ Discovered {len(self.leads)} companies\n")
            
            # Run all phases (Domain extraction -> Scraping -> Summarization -> Email)
            log_section("PHASE 1: DOMAIN EXTRACTION", "INFO")
            self.leads = self._run_domain_extraction()
            print()

            log_section("PHASE 2: WEBSITE SCRAPING", "INFO")
            self.leads = self._run_website_scraping()
            print()

            log_section("PHASE 3: AI SUMMARIZATION", "INFO")
            self.leads = self._run_summarization()
            print()

            log_section("PHASE 4: EMAIL GENERATION", "INFO")
            self.leads = self._run_email_generation()
            print()
            
            # Phase 5: Google Sheets (APPEND mode)
            if update_sheets:
                log_section("PHASE 5: GOOGLE SHEETS UPDATE", "INFO")
                self._run_sheets_integration()
                print()
            
            # Final summary
            results = self._get_results()
            results = self._finalize_pipeline(results)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return self._get_results()
    
    # ========================================================================
    # PHASE 1: LEAD INGESTION
    # ========================================================================
    
    def _run_ingestion(self, source: str, csv_path: str = None) -> List[Dict]:
        """Run lead ingestion phase (Scenario 1)."""
        try:
            if source == 'csv':
                if csv_path:
                    path_to_use = csv_path
                elif SAMPLE_CSV.exists():
                    path_to_use = str(SAMPLE_CSV)
                    self.logger.info(
                        f"No --csv path given; using default: {path_to_use}"
                    )
                else:
                    raise ValueError(
                        "CSV path required: pass --csv <path> or place your "
                        "data at data/sample_leads.csv"
                    )

                self.logger.info(f"Reading from CSV: {path_to_use}")
                leads = self.ingestion.read_from_csv(path_to_use)

            elif source == 'google_sheets':
                self.logger.info("Reading from Google Sheets")
                leads = self.sheets.read_leads()

            else:
                raise ValueError(f"Unknown source: {source}")

            if not leads:
                self.logger.error("No leads loaded!")
                return []

            # Remove duplicates
            self.ingestion.leads = leads
            leads = self.ingestion.remove_duplicates()

            self.logger.info(f"Ingestion complete: {len(leads)} leads")
            return leads

        except Exception as e:
            self.logger.error(f"Ingestion failed: {e}")
            raise
    
    # ========================================================================
    # PHASE 2: DOMAIN EXTRACTION
    # ========================================================================
    
    def _run_domain_extraction(self) -> List[Dict]:
        """Run domain extraction phase"""
        try:
            results = self.extractor.extract_domains_batch(self.leads)
            
            # Count results
            successful = sum(
                1 for r in results if r.get('extracted_domain')
            )
            failed = len(results) - successful
            
            self.logger.info(
                f"✅ Domain extraction: {successful} success, {failed} failed"
            )
            return results
        
        except Exception as e:
            self.logger.error(f"❌ Domain extraction failed: {e}")
            raise
    
    # ========================================================================
    # PHASE 3: WEBSITE SCRAPING
    # ========================================================================
    
    def _run_website_scraping(self) -> List[Dict]:
        """Run website scraping phase"""
        try:
            results = self.scraper.scrape_websites_batch(self.leads)
            
            # Count results
            successful = sum(
                1 for r in results if r.get('scrape_status') == 'success'
            )
            failed = sum(
                1 for r in results if r.get('scrape_status') == 'failed'
            )
            
            self.logger.info(
                f"✅ Website scraping: {successful} success, {failed} failed"
            )
            return results
        
        except Exception as e:
            self.logger.error(f"❌ Website scraping failed: {e}")
            raise
    
    # ========================================================================
    # PHASE 4: AI SUMMARIZATION
    # ========================================================================
    
    def _run_summarization(self) -> List[Dict]:
        """Run AI summarization phase"""
        try:
            results = self.summarizer.summarize_batch(self.leads)
            
            # Count results
            successful = sum(
                1 for r in results if r.get('summary_status') == 'success'
            )
            failed = sum(
                1 for r in results if r.get('summary_status') == 'failed'
            )
            skipped = sum(
                1 for r in results if r.get('summary_status') == 'skipped'
            )
            
            self.logger.info(
                f"✅ Summarization: {successful} success, "
                f"{failed} failed, {skipped} skipped"
            )
            return results
        
        except Exception as e:
            self.logger.error(f"❌ Summarization failed: {e}")
            raise
    
    # ========================================================================
    # PHASE 5: EMAIL GENERATION
    # ========================================================================
    
    def _run_email_generation(self) -> List[Dict]:
        """Run email generation phase"""
        try:
            results = self.email_gen.generate_emails_batch(self.leads)
            
            # Count results
            successful = sum(
                1 for r in results if r.get('email_status') == 'success'
            )
            failed = sum(
                1 for r in results if r.get('email_status') == 'failed'
            )
            skipped = sum(
                1 for r in results if r.get('email_status') == 'skipped'
            )
            
            self.logger.info(
                f"✅ Email generation: {successful} success, "
                f"{failed} failed, {skipped} skipped"
            )
            return results
        
        except Exception as e:
            self.logger.error(f"❌ Email generation failed: {e}")
            raise
    
    # ========================================================================
    # PHASE 6: GOOGLE SHEETS INTEGRATION
    # ========================================================================
    
    def _run_sheets_integration(self) -> bool:
        """Run Google Sheets integration phase (APPEND mode - preserving old values)"""
        try:
            # Get worksheet
            self.sheets.get_worksheet()
            
            # DON'T CLEAR - Check if headers exist
            current_rows = self.sheets.worksheet.get_all_values()
            
            if not current_rows:
                # First time - add headers
                headers = [
                    'company_name',
                    'email',
                    'website',
                    'industry',
                    'extracted_domain',
                    'website_content',
                    'business_summary',
                    'generated_email',
                    'email_status',
                    'processed_date'
                ]
                self.sheets.initialize_sheet(headers)
                self.logger.info("✅ Headers added to empty sheet")
            
            # Helper to convert HTML to simple plain text if needed
            import re
            def clean_html(text):
                if not text:
                    return ''
                clean = re.sub('<[^<]+?>', '', str(text))
                return clean.strip()

            # APPEND new data (don't clear old)
            for lead in self.leads:
                email_content = clean_html(lead.get('generated_email', ''))
                row_data = [
                    lead.get('company_name', ''),
                    lead.get('email', ''),
                    lead.get('website', ''),
                    lead.get('industry', ''),
                    lead.get('extracted_domain', ''),
                    lead.get('website_content', ''),
                    lead.get('business_summary', ''),
                    email_content,
                    lead.get('email_status', 'pending'),
                    time.strftime('%Y-%m-%d %H:%M:%S'),
                ]
                self.sheets.worksheet.append_row(row_data)
            
            self.logger.info(
                f"✅ Appended {len(self.leads)} new rows to Google Sheets (old data preserved)"
            )
            self.logger.info(
                f"📊 View results: {self.sheets.get_sheet_url()}"
            )
            return True
        
        except Exception as e:
            error_msg = f"Failed to append to sheets: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False
    
    # ========================================================================
    # RESULTS & REPORTING
    # ========================================================================
    
    def _get_results(self) -> Dict:
        """Get pipeline results"""
        elapsed_time = (
            time.time() - self.start_time if self.start_time else 0
        )
        
        return {
            'total_leads': len(self.leads),
            'processed_leads': len(
                [l for l in self.leads if l.get('email_status') == 'success']
            ),
            'elapsed_time': elapsed_time,
            'errors': error_tracker.get_error_summary(),
            'leads': self.leads,
        }
    
    def _finalize_pipeline(self, results: Dict) -> Dict:
        """
        Finalize pipeline: export results and print summary
        """
        # Export to results.csv
        log_section("EXPORTING RESULTS", "INFO")
        
        self.results_exporter.export_results(
            self.leads,
            scenario=str(self._current_scenario),
            industry=self._current_industry,
            include_failed=False
        )
        
        # Get results summary
        results_summary = self.results_exporter.get_results_summary(self.leads)
        
        print()
        self._print_summary(results, results_summary)
        
        return results

    def _print_summary(self, results: Dict, results_summary: Dict):
        """Print final summary with statistics"""
        
        print("\n" + "="*70)
        print("FINAL SUMMARY")
        print("="*70)
        
        print(f"\n📊 PIPELINE STATISTICS:")
        print(f"  Total Leads Processed: {results_summary['total_leads']}")
        print(f"  ✅ Successful: {results_summary['successful']}")
        print(f"  ⏭️  Skipped: {results_summary['skipped']}")
        print(f"  ❌ Failed: {results_summary['failed']}")
        print(f"  Success Rate: {results_summary['success_rate']:.1f}%")
        print(f"  Time Elapsed: {results['elapsed_time']:.2f} seconds")
        
        print(f"\n📁 OUTPUT FILES:")
        print(f"  Results CSV: {results_summary['results_file']}")
        print(f"  Google Sheet: {self.sheets.get_sheet_url()}")
        
        if results['errors'] and results['errors']['total_errors'] > 0:
            print(f"\n⚠️  ERRORS: {results['errors']['total_errors']}")
            for error_type, count in results['errors']['errors_by_type'].items():
                print(f"      - {error_type}: {count}")
        
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETE!")
        print("="*70)



# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AI Lead Generation Pipeline'
    )
    
    # Scenario selection
    parser.add_argument(
        '--scenario',
        choices=['1', '2'],
        default='1',
        help='Scenario 1 (provided list) or 2 (auto-discover)'
    )
    
    # Scenario 1 args
    parser.add_argument(
        '--source',
        choices=['google_sheets', 'csv'],
        default='google_sheets',
        help='Data source for Scenario 1'
    )
    parser.add_argument('--csv', type=str, help='CSV file path')
    parser.add_argument('--max-leads', type=int, help='Maximum leads to process in Scenario 1')
    
    # Scenario 2 args
    parser.add_argument(
        '--industry',
        type=str,
        help='Industry for Scenario 2 (e.g., "Healthcare AI")'
    )
    parser.add_argument(
        '--topic',
        type=str,
        help='GitHub topic (e.g., "healthcare-ai")'
    )
    parser.add_argument(
        '--location',
        type=str,
        help='Location filter'
    )
    parser.add_argument(
        '--num-results',
        type=int,
        default=50,
        help='Number of companies to find (Scenario 2)'
    )
    
    parser.add_argument(
        '--no-sheets-update',
        action='store_true',
        help='Do not update Google Sheets'
    )
    
    args = parser.parse_args()
    
    pipeline = LeadGenerationPipeline()
    
    if args.scenario == '2':
        # Scenario 2
        results = pipeline.run_pipeline_scenario2(
            industry=args.industry or "Technology",
            topic=args.topic,
            location=args.location,
            num_results=args.num_results,
            update_sheets=not args.no_sheets_update
        )
    else:
        # Scenario 1
        results = pipeline.run_pipeline(
            source=args.source,
            csv_path=args.csv,
            max_leads=args.max_leads,
            update_sheets=not args.no_sheets_update
        )
    
    sys.exit(0 if results['processed_leads'] > 0 else 1)



# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("\n" + "="*70)
        print("AI LEAD GENERATION PIPELINE")
        print("="*70 + "\n")

        pipeline = LeadGenerationPipeline()

        # Smart default: use sample CSV if it exists, else Google Sheets
        if SAMPLE_CSV.exists():
            print(f"  Auto-detected: using {SAMPLE_CSV}\n")
            results = pipeline.run_pipeline(
                source='csv',
                csv_path=str(SAMPLE_CSV),
                update_sheets=True,
            )
        else:
            print("  data/sample_leads.csv not found — reading from Google Sheets\n")
            results = pipeline.run_pipeline(
                source='google_sheets',
                update_sheets=True,
            )

        print("\n" + "="*70)
        print("Pipeline completed!")
        print("="*70 + "\n")