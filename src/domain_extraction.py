"""
domain_extraction.py - Domain Extraction
=========================================
Extract domain names from:
1. Email addresses
2. Website URLs
3. Company names (fallback)

Normalize and validate domains.
"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from .config import MAX_LEADS_PER_BATCH
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    DomainExtractionError,
)

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class DomainExtractor:
    """
    Extract and normalize domain names from various sources
    """
    
    def __init__(self):
        """Initialize domain extractor"""
        self.logger = logger
        self.error_tracker = error_tracker
    
    # ========================================================================
    # MAIN EXTRACTION METHOD
    # ========================================================================
    
    def extract_domain(self, lead: Dict) -> Dict:
        """
        Extract domain from lead data using priority order:
        1. If domain provided directly → Use it
        2. If email provided → Extract from email
        3. If website provided → Extract from URL
        4. If none → Skip and log error
        
        Args:
            lead (Dict): Lead data with company_name, email, website
        
        Returns:
            Dict: Lead with extracted_domain and domain_source added
        """
        try:
            company_name = lead.get('company_name', '')
            email = lead.get('email', '').strip()
            website = lead.get('website', '').strip()
            
            # Priority 1: Extract from email
            if email:
                domain, source = self._extract_from_email(email)
                if domain:
                    lead['extracted_domain'] = domain
                    lead['domain_source'] = source
                    self.logger.debug(
                        f"{company_name}: Domain extracted from email: {domain}"
                    )
                    return lead
            
            # Priority 2: Extract from website
            if website:
                domain, source = self._extract_from_url(website)
                if domain:
                    lead['extracted_domain'] = domain
                    lead['domain_source'] = source
                    self.logger.debug(
                        f"{company_name}: Domain extracted from website: {domain}"
                    )
                    return lead
            
            # Priority 3: Fallback to company name
            if company_name:
                domain, source = self._extract_from_company_name(company_name)
                if domain:
                    lead['extracted_domain'] = domain
                    lead['domain_source'] = source
                    self.logger.debug(
                        f"{company_name}: Domain extracted from company name: {domain}"
                    )
                    return lead
            
            # No domain found
            lead['extracted_domain'] = ''
            lead['domain_source'] = 'none'
            error_msg = f"Could not extract domain for: {company_name}"
            self.logger.warning(error_msg)
            self.error_tracker.add_error(
                company_name,
                "DomainExtractionError",
                error_msg,
                "domain_extraction"
            )
            
            return lead
        
        except Exception as e:
            self.logger.error(f"Error extracting domain: {e}")
            lead['extracted_domain'] = ''
            lead['domain_source'] = 'error'
            self.error_tracker.add_error(
                lead.get('company_name', 'Unknown'),
                "DomainExtractionError",
                str(e),
                "domain_extraction"
            )
            return lead
    
    # ========================================================================
    # EXTRACTION FROM EMAIL
    # ========================================================================
    
    def _extract_from_email(self, email: str) -> Tuple[Optional[str], str]:
        """
        Extract domain from email address
        
        Example:
            contact@techstartup.com → techstartup.com
        
        Args:
            email (str): Email address
        
        Returns:
            Tuple[str, str]: (domain, source) or (None, 'email_failed')
        """
        try:
            if not email or '@' not in email:
                return None, 'email_failed'
            
            # Extract domain part after @
            domain = email.split('@')[1].strip().lower()
            
            # Validate
            if not domain or '.' not in domain:
                return None, 'email_failed'
            
            # Normalize (remove www if present)
            domain = self._normalize_domain(domain)
            
            return domain, 'email'
        
        except Exception:
            return None, 'email_failed'
    
    # ========================================================================
    # EXTRACTION FROM URL
    # ========================================================================
    
    def _extract_from_url(self, website: str) -> Tuple[Optional[str], str]:
        """
        Extract domain from website URL
        
        Examples:
            https://www.techstartup.com → techstartup.com
            techstartup.com → techstartup.com
            www.techstartup.com → techstartup.com
        
        Args:
            website (str): Website URL
        
        Returns:
            Tuple[str, str]: (domain, source) or (None, 'url_failed')
        """
        try:
            if not website:
                return None, 'url_failed'
            
            # Add https if missing
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            
            # Parse URL
            parsed = urlparse(website)
            netloc = parsed.netloc or parsed.path
            
            if not netloc:
                return None, 'url_failed'
            
            # Extract domain
            domain = netloc.lower()
            
            # Remove www prefix
            domain = self._normalize_domain(domain)
            
            if '.' not in domain:
                return None, 'url_failed'
            
            return domain, 'website'
        
        except Exception:
            return None, 'url_failed'
    
    # ========================================================================
    # EXTRACTION FROM COMPANY NAME
    # ========================================================================
    
    def _extract_from_company_name(
        self, company_name: str
    ) -> Tuple[Optional[str], str]:
        """
        Extract domain from company name (fallback)
        
        Examples:
            TechStartup Inc → techstartup.com
            DataCorp Solutions → datacorp.com
        
        Args:
            company_name (str): Company name
        
        Returns:
            Tuple[str, str]: (domain, source) or (None, 'company_failed')
        """
        try:
            if not company_name:
                return None, 'company_failed'
            
            # Convert to lowercase
            name = company_name.lower()
            
            # Remove common company suffixes
            suffixes = [
                ' inc', ' ltd', ' llc', ' corp', ' corporation',
                ' solutions', ' systems', ' technologies', ' tech',
                ' labs', ' ai', ' pro', ' services', ' group',
                ' company', ' co', ' startup', ' hub', ' io'
            ]
            
            for suffix in suffixes:
                if name.endswith(suffix):
                    name = name[:-len(suffix)].strip()
            
            # Remove special characters, keep only alphanumeric and hyphens
            name = re.sub(r'[^a-z0-9\-]', '', name)
            
            if not name:
                return None, 'company_failed'
            
            # Add .com
            domain = f"{name}.com"
            
            return domain, 'company_name'
        
        except Exception:
            return None, 'company_failed'
    
    # ========================================================================
    # DOMAIN NORMALIZATION
    # ========================================================================
    
    def _normalize_domain(self, domain: str) -> str:
        """
        Normalize domain:
        - Lowercase
        - Remove www prefix
        - Remove trailing slashes
        - Remove port numbers
        
        Args:
            domain (str): Raw domain
        
        Returns:
            str: Normalized domain
        """
        if not domain:
            return ''
        
        domain = domain.lower().strip()
        
        # Remove protocol if present
        domain = domain.replace('http://', '').replace('https://', '')
        
        # Remove trailing slashes
        domain = domain.rstrip('/')
        
        # Remove port numbers
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove trailing slashes again
        domain = domain.rstrip('/')
        
        return domain
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def extract_domains_batch(self, leads: list) -> list:
        """
        Extract domains for a batch of leads
        
        Args:
            leads (list): List of lead dictionaries
        
        Returns:
            list: Leads with extracted domains
        """
        self.logger.info(f"Extracting domains for {len(leads)} leads...")
        
        processed_leads = []
        successful = 0
        failed = 0
        
        for i, lead in enumerate(leads, 1):
            result = self.extract_domain(lead)
            processed_leads.append(result)
            
            if result.get('extracted_domain'):
                successful += 1
            else:
                failed += 1
            
            # Log progress
            if i % 5 == 0:
                self.logger.info(
                    f"Progress: {i}/{len(leads)} - "
                    f"Success: {successful}, Failed: {failed}"
                )
        
        self.logger.info(
            f"✅ Domain extraction complete! "
            f"Success: {successful}, Failed: {failed}"
        )
        
        return processed_leads
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def is_valid_domain(self, domain: str) -> bool:
        """
        Check if domain is valid
        
        Args:
            domain (str): Domain to validate
        
        Returns:
            bool: True if valid
        """
        if not domain:
            return False
        
        # Must contain at least one dot
        if '.' not in domain:
            return False
        
        # Must not start/end with dot or hyphen
        if domain.startswith('.') or domain.endswith('.'):
            return False
        if domain.startswith('-') or domain.endswith('-'):
            return False
        
        # Must be lowercase
        if domain != domain.lower():
            return False
        
        return True


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test domain extraction
    """
    print("\n" + "="*60)
    print("TESTING DOMAIN EXTRACTION")
    print("="*60 + "\n")
    
    extractor = DomainExtractor()
    
    # Test cases
    test_leads = [
        {
            'company_name': 'TechStartup Inc',
            'email': 'contact@techstartup.com',
            'website': 'https://techstartup.com',
            'industry': 'Healthcare'
        },
        {
            'company_name': 'DataCorp Solutions',
            'email': 'hello@datacorp.com',
            'website': '',
            'industry': 'Finance'
        },
        {
            'company_name': 'AI Systems Ltd',
            'email': '',
            'website': 'www.aisystems.com',
            'industry': 'SaaS'
        },
        {
            'company_name': 'Unknown Company',
            'email': '',
            'website': '',
            'industry': 'Tech'
        },
    ]
    
    print("Test 1: Individual domain extraction")
    for lead in test_leads:
        result = extractor.extract_domain(lead)
        print(f"\n  Company: {result['company_name']}")
        print(f"  Email: {result['email']}")
        print(f"  Website: {result['website']}")
        print(f"  Extracted Domain: {result['extracted_domain']}")
        print(f"  Domain Source: {result['domain_source']}")
    
    print("\n" + "-"*60)
    print("\nTest 2: Batch extraction")
    results = extractor.extract_domains_batch(test_leads)
    print(f"\n✅ Processed {len(results)} leads")
    
    # Show error report
    error_summary = error_tracker.get_error_summary()
    if error_summary:
        print(f"\n⚠️  Errors: {error_summary['total_errors']}")
    
    print("\n" + "="*60)
    print("✅ Domain extraction test completed!")
    print("="*60 + "\n")