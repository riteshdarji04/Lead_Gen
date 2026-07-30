"""
website_scraper.py - Website Content Scraper
==============================================
Scrape website content from domains using:
- requests (HTTP requests)
- BeautifulSoup (HTML parsing)

Extract text content and business information.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

from .config import (
    WEBSITE_TIMEOUT_SECONDS,
    MAX_WEBSITE_CONTENT_LENGTH,
    REQUEST_DELAY,
    MAX_RETRIES,
    USER_AGENT,
)
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    WebScrapingError,
)

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class WebsiteScraper:
    """
    Scrape website content and extract business information
    """
    
    def __init__(self):
        """Initialize website scraper"""
        self.logger = logger
        self.error_tracker = error_tracker
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    # ========================================================================
    # MAIN SCRAPING METHOD
    # ========================================================================
    
    def scrape_website(self, domain: str, company_name: str = '', full_url: str = '') -> Dict:
        """
        Scrape website content from domain or full_url
        """
        try:
            self.logger.info(f"Scraping website: {domain or full_url}")
            
            # Construct URL
            url = full_url if (full_url and full_url.startswith('http')) else self._construct_url(domain)

            
            # Fetch webpage
            html_content = self._fetch_page(url)
            
            if not html_content:
                raise WebScrapingError(f"Failed to fetch content from {url}")
            
            # Parse HTML
            text_content = self._parse_html(html_content)
            
            if not text_content:
                raise WebScrapingError(f"No text content extracted from {url}")
            
            # Limit content length
            text_content = text_content[:MAX_WEBSITE_CONTENT_LENGTH]
            
            self.logger.info(
                f"✅ Successfully scraped {domain} "
                f"({len(text_content)} characters)"
            )
            
            return {
                'domain': domain,
                'website_content': text_content,
                'website_url': url,
                'scrape_status': 'success',
                'content_length': len(text_content),
            }
        
        except WebScrapingError as e:
            error_msg = str(e)
            self.logger.warning(f"⚠️  Scraping error for {domain}: {error_msg}")
            self.error_tracker.add_error(
                company_name or domain,
                "WebScrapingError",
                error_msg,
                "website_scraping"
            )
            return {
                'domain': domain,
                'website_content': '',
                'website_url': '',
                'scrape_status': 'failed',
                'content_length': 0,
                'error': error_msg,
            }
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"❌ Error scraping {domain}: {error_msg}")
            self.error_tracker.add_error(
                company_name or domain,
                "WebScrapingError",
                error_msg,
                "website_scraping"
            )
            return {
                'domain': domain,
                'website_content': '',
                'website_url': '',
                'scrape_status': 'failed',
                'content_length': 0,
                'error': error_msg,
            }
        
        finally:
            # Be respectful - add delay between requests
            time.sleep(REQUEST_DELAY)
    
    # ========================================================================
    # URL CONSTRUCTION
    # ========================================================================
    
    def _construct_url(self, domain: str) -> str:
        """
        Construct full URL from domain
        
        Args:
            domain (str): Domain name
        
        Returns:
            str: Full URL with protocol
        """
        domain = domain.strip()
        
        # Add protocol if missing
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        return domain
    
    # ========================================================================
    # PAGE FETCHING
    # ========================================================================
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch webpage with fallback to HTTP and SSL tolerance
        """
        urls_to_try = [url]
        if url.startswith('https://'):
            urls_to_try.append(url.replace('https://', 'http://'))

        for target_url in urls_to_try:
            for attempt in range(MAX_RETRIES):
                try:
                    self.logger.debug(f"Fetching URL (attempt {attempt + 1}): {target_url}")
                    
                    response = self.session.get(
                        target_url,
                        timeout=WEBSITE_TIMEOUT_SECONDS,
                        allow_redirects=True,
                        verify=False,
                    )
                    
                    # Check status code
                    if response.status_code == 200 and response.text.strip():
                        return response.text
                    
                    elif response.status_code == 404:
                        break  # No need to retry 404 on same URL
                    
                    elif response.status_code in [403, 401]:
                        break
                    
                    elif response.status_code >= 500:
                        time.sleep(1)
                        continue
                    
                    else:
                        time.sleep(1)
                        continue
                
                except requests.Timeout:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                
                except requests.ConnectionError:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                
                except requests.RequestException:
                    break
        
        return None
    
    # ========================================================================
    # HTML PARSING
    # ========================================================================
    
    def _parse_html(self, html_content: str) -> str:
        """
        Parse HTML and extract text content
        
        Args:
            html_content (str): Raw HTML
        
        Returns:
            str: Extracted text content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        
        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}")
            return ""
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def scrape_websites_batch(self, leads: list) -> list:
        """
        Scrape websites for a batch of leads
        
        Args:
            leads (list): List of lead dictionaries with extracted_domain
        
        Returns:
            list: Leads with website_content added
        """
        self.logger.info(f"Scraping {len(leads)} websites...")
        
        results = []
        successful = 0
        failed = 0
        
        for i, lead in enumerate(leads, 1):
            domain = lead.get('extracted_domain', '')
            company_name = lead.get('company_name', '')
            
            if not domain:
                self.logger.debug(
                    f"Skipping {company_name}: No domain extracted"
                )
                lead['website_content'] = ''
                lead['scrape_status'] = 'skipped'
                results.append(lead)
                continue
            
            # Scrape
            full_url = lead.get('website', '')
            scrape_result = self.scrape_website(domain, company_name, full_url=full_url)
            
            # Merge results
            lead.update(scrape_result)
            results.append(lead)
            
            # Count
            if scrape_result['scrape_status'] == 'success':
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
            f"✅ Website scraping complete! "
            f"Success: {successful}, Failed: {failed}"
        )
        
        return results
    
    # ========================================================================
    # CONTENT EXTRACTION (Business Info)
    # ========================================================================
    
    def extract_business_info(self, content: str) -> Dict:
        """
        Extract key business information from website content
        
        Args:
            content (str): Website text content
        
        Returns:
            Dict: Extracted business info
        """
        info = {
            'mentions_ai': False,
            'mentions_automation': False,
            'mentions_analytics': False,
            'mentions_saas': False,
            'content_length': len(content),
        }
        
        content_lower = content.lower()
        
        # Check for keywords
        if 'ai' in content_lower or 'artificial intelligence' in content_lower:
            info['mentions_ai'] = True
        
        if 'automat' in content_lower:
            info['mentions_automation'] = True
        
        if 'analytic' in content_lower or 'data' in content_lower:
            info['mentions_analytics'] = True
        
        if 'saas' in content_lower or 'software as a service' in content_lower:
            info['mentions_saas'] = True
        
        return info


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test website scraping
    """
    print("\n" + "="*60)
    print("TESTING WEBSITE SCRAPER")
    print("="*60 + "\n")
    
    scraper = WebsiteScraper()
    
    # Test domains
    test_domains = [
        {
            'company_name': 'TechStartup Inc',
            'extracted_domain': 'techstartup.com',
        },
        {
            'company_name': 'DataCorp Solutions',
            'extracted_domain': 'datacorp.com',
        },
        {
            'company_name': 'OpenAI',
            'extracted_domain': 'openai.com',
        },
    ]
    
    print("Test 1: Scraping individual websites")
    for domain_info in test_domains:
        result = scraper.scrape_website(
            domain_info['extracted_domain'],
            domain_info['company_name']
        )
        
        print(f"\n  Company: {domain_info['company_name']}")
        print(f"  Domain: {domain_info['extracted_domain']}")
        print(f"  Status: {result['scrape_status']}")
        print(f"  Content Length: {result['content_length']} chars")
        
        if result['website_content']:
            preview = result['website_content'][:150]
            print(f"  Preview: {preview}...")
    
    print("\n" + "-"*60)
    print("\nTest 2: Batch scraping")
    results = scraper.scrape_websites_batch(test_domains)
    print(f"\n✅ Scraped {len(results)} websites")
    
    # Show error report
    error_summary = error_tracker.get_error_summary()
    if error_summary:
        print(f"\n⚠️  Errors: {error_summary['total_errors']}")
    
    print("\n" + "="*60)
    print("✅ Website scraper test completed!")
    print("="*60 + "\n")