"""
results_exporter.py - Results Export Module
============================================
Export processed leads to results.csv
Includes: successful leads, skipped leads
Excludes: leads that failed completely

Creates data/output/results.csv with current session results.
"""

import csv
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from .config import OUTPUT_DIR
from .error_handler import LoggerSetup

logger = LoggerSetup.get_logger(__name__)


class ResultsExporter:
    """
    Export pipeline results to CSV
    """
    
    def __init__(self):
        """Initialize results exporter"""
        self.logger = logger
        self.output_dir = OUTPUT_DIR
        self.results_file = self.output_dir / "results.csv"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # EXPORT RESULTS
    # ========================================================================
    
    def export_results(
        self,
        leads: List[Dict],
        scenario: str = "1",
        industry: str = "",
        include_failed: bool = False
    ) -> bool:
        """
        Export processed leads to results.csv
        
        Args:
            leads (List[Dict]): All processed leads
            scenario (str): Scenario number (1 or 2)
            industry (str): Industry filter (for Scenario 2)
            include_failed (bool): Include failed leads in results
        
        Returns:
            bool: True if successful
        """
        try:
            # Filter leads to export
            filtered_leads = self._filter_leads(leads, include_failed)
            
            if not filtered_leads:
                self.logger.warning("No leads to export to results.csv")
                return False
            
            # Prepare data
            rows = self._prepare_rows(filtered_leads, scenario, industry)
            
            # Write to CSV
            success = self._write_csv(rows)
            
            if success:
                self.logger.info(
                    f"✅ Exported {len(filtered_leads)} results to "
                    f"{self.results_file}"
                )
            
            return success
        
        except Exception as e:
            self.logger.error(f"❌ Error exporting results: {e}")
            return False
    
    # ========================================================================
    # FILTER LEADS
    # ========================================================================
    
    def _filter_leads(
        self,
        leads: List[Dict],
        include_failed: bool = False
    ) -> List[Dict]:
        """
        Filter leads for export
        
        Include:
        - Successful leads (email_status = 'success')
        - Skipped leads (email_status = 'skipped')
        
        Exclude (unless include_failed=True):
        - Failed leads (email_status = 'failed')
        
        Args:
            leads (List[Dict]): All leads
            include_failed (bool): Include failed leads
        
        Returns:
            List[Dict]: Filtered leads
        """
        filtered = []
        
        for lead in leads:
            status = lead.get('email_status', 'pending')
            
            # Include successful and skipped
            if status in ['success', 'skipped']:
                filtered.append(lead)
            
            # Include failed if requested
            elif status == 'failed' and include_failed:
                filtered.append(lead)
        
        return filtered
    
    # ========================================================================
    # PREPARE ROWS FOR CSV
    # ========================================================================
    
    def _prepare_rows(
        self,
        leads: List[Dict],
        scenario: str,
        industry: str
    ) -> List[Dict]:
        """
        Prepare rows for CSV export
        
        Args:
            leads (List[Dict]): Filtered leads
            scenario (str): Scenario number
            industry (str): Industry filter
        
        Returns:
            List[Dict]: Rows to write
        """
        rows = []
        
        for i, lead in enumerate(leads, 1):
            # Extract email preview (first 50 chars)
            email_preview = ""
            if lead.get('generated_email'):
                # Remove HTML tags for preview
                import re
                text = re.sub('<[^<]+?>', '', lead['generated_email'])
                email_preview = text[:100].strip()
            
            row = {
                'ID': i,
                'Company Name': lead.get('company_name', ''),
                'Email': lead.get('email', ''),
                'Website': lead.get('website', ''),
                'Industry': lead.get('industry', industry),
                'Extracted Domain': lead.get('extracted_domain', ''),
                'Business Summary': lead.get('business_summary', ''),
                'Email Preview': email_preview,
                'Email Status': lead.get('email_status', 'pending'),
                'Scrape Status': lead.get('scrape_status', ''),
                'Summary Status': lead.get('summary_status', ''),
                'Processed Date': lead.get('processed_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'Scenario': scenario,
            }
            rows.append(row)
        
        return rows
    
    # ========================================================================
    # WRITE CSV FILE
    # ========================================================================
    
    def _write_csv(self, rows: List[Dict]) -> bool:
        """
        Write rows to CSV file
        
        Args:
            rows (List[Dict]): Rows to write
        
        Returns:
            bool: True if successful
        """
        try:
            if not rows:
                return False
            
            # Get field names from first row
            fieldnames = list(rows[0].keys())
            
            # Write CSV
            with open(self.results_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            self.logger.info(f"✅ CSV file created: {self.results_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error writing CSV: {e}")
            return False
    
    # ========================================================================
    # GET RESULTS SUMMARY
    # ========================================================================
    
    def get_results_summary(self, leads: List[Dict]) -> Dict:
        """
        Get summary statistics for results
        
        Args:
            leads (List[Dict]): All processed leads
        
        Returns:
            Dict: Summary statistics
        """
        summary = {
            'total_leads': len(leads),
            'successful': 0,
            'skipped': 0,
            'failed': 0,
            'success_rate': 0,
            'results_file': str(self.results_file),
        }
        
        for lead in leads:
            status = lead.get('email_status', 'pending')
            if status == 'success':
                summary['successful'] += 1
            elif status == 'skipped':
                summary['skipped'] += 1
            elif status == 'failed':
                summary['failed'] += 1
        
        # Calculate success rate (successful + skipped, not failed)
        processed = summary['successful'] + summary['skipped']
        if summary['total_leads'] > 0:
            summary['success_rate'] = (processed / summary['total_leads']) * 100
        
        return summary
    
    # ========================================================================
    # FILE MANAGEMENT
    # ========================================================================
    
    def get_results_file_path(self) -> Path:
        """Get path to results CSV file"""
        return self.results_file
    
    def results_file_exists(self) -> bool:
        """Check if results file exists"""
        return self.results_file.exists()
    
    def get_results_file_size(self) -> int:
        """Get size of results file in bytes"""
        if self.results_file.exists():
            return self.results_file.stat().st_size
        return 0
    
    def clear_results(self) -> bool:
        """Clear results file"""
        try:
            if self.results_file.exists():
                self.results_file.unlink()
                self.logger.info("✅ Results file cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing results: {e}")
            return False


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test results export
    """
    print("\n" + "="*60)
    print("TESTING RESULTS EXPORTER")
    print("="*60 + "\n")
    
    # Sample leads
    test_leads = [
        {
            'company_name': 'Company A',
            'email': 'contact@a.com',
            'website': 'https://a.com',
            'industry': 'SaaS',
            'extracted_domain': 'a.com',
            'business_summary': 'Sample business summary',
            'generated_email': '<html><body>Sample email</body></html>',
            'email_status': 'success',
            'scrape_status': 'success',
            'summary_status': 'success',
        },
        {
            'company_name': 'Company B',
            'email': '',
            'website': '',
            'industry': 'Tech',
            'extracted_domain': '',
            'business_summary': '',
            'generated_email': '',
            'email_status': 'skipped',
            'scrape_status': 'failed',
            'summary_status': 'skipped',
        },
    ]
    
    # Export results
    exporter = ResultsExporter()
    
    print("Exporting results...")
    success = exporter.export_results(
        test_leads,
        scenario="1",
        industry="SaaS"
    )
    
    if success:
        print("✅ Export successful")
        
        # Print summary
        summary = exporter.get_results_summary(test_leads)
        print(f"\nResults Summary:")
        print(f"  Total Leads: {summary['total_leads']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Skipped: {summary['skipped']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  File: {summary['results_file']}")
    else:
        print("❌ Export failed")
    
    print("\n" + "="*60 + "\n")