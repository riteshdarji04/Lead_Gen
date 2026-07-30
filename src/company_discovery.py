# """
# company_discovery.py - Company Discovery Module
# ===============================================
# Find companies based on search criteria using:
# - GitHub API (find repos by topic/language)
# - Google Maps scraping (company search)
# - Company website scraping (get contact info)
# """

# import requests
# from typing import List, Dict, Optional
# import re
# from urllib.parse import urljoin
# from bs4 import BeautifulSoup

# from .error_handler import LoggerSetup
# from .config import USER_AGENT

# logger = LoggerSetup.get_logger(__name__)


# class CompanyDiscovery:
#     """
#     Discover companies based on search criteria
#     """
    
#     def __init__(self):
#         """Initialize discovery"""
#         self.logger = logger
#         self.session = requests.Session()
#         self.session.headers.update({'User-Agent': USER_AGENT})
    
#     # ========================================================================
#     # GITHUB API - Find companies from trending repos
#     # ========================================================================
    
#     def discover_from_github(
#         self,
#         topic: str,
#         language: str = 'python',
#         stars_min: int = 100
#     ) -> List[Dict]:
#         """
#         Find companies/projects from GitHub trending repos
#         """
#         try:
#             self.logger.info(
#                 f"Searching GitHub for topic='{topic}', language='{language}'"
#             )
            
#             # GitHub API search
#             url = "https://api.github.com/search/repositories"
#             params = {
#                 'q': f'topic:{topic} stars:>{stars_min}',
#                 'sort': 'stars',
#                 'order': 'desc',
#                 'per_page': 50
#             }
            
#             response = requests.get(url, params=params, timeout=10)
#             response.raise_for_status()
            
#             data = response.json()
#             companies = []
            
#             for repo in data.get('items', []):
#                 owner = repo['full_name'].split('/')[0]
#                 raw_homepage = repo.get('homepage') or ''
#                 homepage = raw_homepage.strip()
#                 if homepage and not homepage.startswith('http'):
#                     homepage = 'https://' + homepage
                
#                 # Only keep real company websites (ignore missing or github.com links)
#                 if homepage and 'github.com' not in homepage:
#                     company = {
#                         'company_name': owner,
#                         'website': homepage,
#                         'email': f"contact@{owner.lower()}.com",
#                         'industry': topic.replace('-', ' ').title() if topic else 'Technology',
#                         'github_url': repo['html_url'],
#                         'stars': repo['stargazers_count'],
#                         'description': repo.get('description', ''),
#                         'discovery_source': 'github',
#                     }
#                     companies.append(company)
            
#             self.logger.info(f"✅ Found {len(companies)} valid web companies from GitHub")
#             return companies
        
#         except Exception as e:
#             self.logger.error(f"Error discovering from GitHub: {e}")
#             return []

#     # ========================================================================
#     # DUCKDUCKGO SEARCH - Free fallback discovery
#     # ========================================================================

#     def discover_from_ddg(
#         self,
#         industry: str,
#         num_results: int = 20
#     ) -> List[Dict]:
#         """
#         Free discovery using DuckDuckGo web search HTML API
#         """
#         try:
#             self.logger.info(f"Searching DuckDuckGo for industry='{industry}'")
#             url = "https://html.duckduckgo.com/html/"
#             headers = {
#                 "User-Agent": USER_AGENT,
#                 "Content-Type": "application/x-www-form-urlencoded"
#             }
#             data = {"q": f"{industry} companies"}
            
#             res = requests.post(url, data=data, headers=headers, timeout=10)
#             if res.status_code != 200:
#                 return []
                
#             soup = BeautifulSoup(res.text, 'html.parser')
#             companies = []
            
#             # Find all result links
#             links = soup.select('a.result__url') or soup.find_all('a', href=True)
            
#             for a in links:
#                 raw_url = a.get('href', '').strip()
#                 target_url = raw_url
#                 if 'uddg=' in raw_url:
#                     from urllib.parse import parse_qs, urlparse
#                     parsed = parse_qs(urlparse(raw_url).query)
#                     target_url = parsed.get('uddg', [''])[0]
                    
#                 if not target_url.startswith('http') or 'duckduckgo.com' in target_url:
#                     continue
                    
#                 from urllib.parse import urlparse
#                 domain = urlparse(target_url).netloc.replace('www.', '')
#                 if not domain or any(ignored in domain for ignored in ['wikipedia.org', 'youtube.com', 'linkedin.com', 'facebook.com', 'twitter.com', 'github.com', 'reddit.com', 'medium.com', 'crunchbase.com']):
#                     continue
                    
#                 comp_name = domain.split('.')[0].capitalize()
#                 companies.append({
#                     'company_name': comp_name,
#                     'website': f"https://{domain}",
#                     'email': f"info@{domain}",
#                     'industry': industry,
#                     'discovery_source': 'duckduckgo'
#                 })
                
#                 if len(companies) >= num_results:
#                     break
                    
#             self.logger.info(f"✅ Found {len(companies)} companies from DuckDuckGo")
#             return companies
            
#         except Exception as e:
#             self.logger.error(f"Error discovering from DuckDuckGo: {e}")
#             return []

#     # ========================================================================
#     # COMBINED DISCOVERY
#     # ========================================================================
    
#     def discover_companies(
#         self,
#         industry: str,
#         topic: str = None,
#         location: str = None,
#         num_results: int = 50
#     ) -> List[Dict]:
#         """
#         Discover companies using multiple free sources
#         """
#         all_companies = []
        
#         # 1. GitHub search if topic provided or as initial search
#         gh_topic = topic or industry.lower().replace(' ', '-')
#         github_companies = self.discover_from_github(
#             topic=gh_topic,
#             stars_min=5
#         )
#         all_companies.extend(github_companies)
        
#         # 2. DuckDuckGo Search (Free fallback if needed)
#         if len(all_companies) < num_results:
#             search_query = f"{industry} {location}".strip() if location else industry
#             ddg_companies = self.discover_from_ddg(
#                 industry=search_query,
#                 num_results=num_results - len(all_companies)
#             )
#             all_companies.extend(ddg_companies)
        
#         # Deduplicate
#         seen_websites = set()
#         unique_companies = []
        
#         for company in all_companies:
#             website = company.get('website', '')
#             if website and website not in seen_websites:
#                 seen_websites.add(website)
#                 unique_companies.append(company)
        
#         self.logger.info(
#             f"✅ Discovered {len(unique_companies)} unique companies"
#         )
        
#         return unique_companies[:num_results]





# # Example usage
# if __name__ == "__main__":
#     discovery = CompanyDiscovery()
    
#     # Example: Find AI healthcare companies
#     companies = discovery.discover_companies(
#         industry="Healthcare",
#         topic="healthcare-ai",
#         location="USA",
#         num_results=50
#     )
    
#     for company in companies[:5]:
#         print(f"- {company['company_name']}: {company.get('website', 'N/A')}")


















"""
company_discovery.py - Company Discovery Module
===============================================
Find companies based on search criteria using:
- GitHub API (find repos by topic/language)
- DuckDuckGo web scraping (company search)
"""

import requests
from typing import List, Dict, Optional
import re
from urllib.parse import parse_qs, urlparse, unquote
from bs4 import BeautifulSoup

from .error_handler import LoggerSetup
from .config import USER_AGENT

logger = LoggerSetup.get_logger(__name__)


class CompanyDiscovery:
    """
    Discover companies based on search criteria
    """
    
    def __init__(self):
        """Initialize discovery"""
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    # ========================================================================
    # GITHUB API - Find companies from trending repos
    # ========================================================================
    
    def discover_from_github(
        self,
        topic: str,
        language: str = 'python',
        stars_min: int = 100
    ) -> List[Dict]:
        """
        Find companies/projects from GitHub trending repos
        """
        try:
            self.logger.info(
                f"Searching GitHub for topic='{topic}', language='{language}'"
            )
            
            url = "https://api.github.com/search/repositories"
            params = {
                'q': f'topic:{topic} stars:>{stars_min}',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 50
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            companies = []
            
            for repo in data.get('items', []):
                owner = repo['full_name'].split('/')[0]
                raw_homepage = repo.get('homepage') or ''
                homepage = raw_homepage.strip()
                if homepage and not homepage.startswith('http'):
                    homepage = 'https://' + homepage
                
                # Only keep real company websites (ignore missing or github.com links)
                if homepage and 'github.com' not in homepage:
                    company = {
                        'company_name': owner,
                        'website': homepage,
                        'email': f"contact@{owner.lower()}.com",
                        'industry': topic.replace('-', ' ').title() if topic else 'Technology',
                        'github_url': repo['html_url'],
                        'stars': repo['stargazers_count'],
                        'description': repo.get('description', ''),
                        'discovery_source': 'github',
                    }
                    companies.append(company)
            
            self.logger.info(f"✅ Found {len(companies)} valid web companies from GitHub")
            return companies
        
        except Exception as e:
            self.logger.error(f"Error discovering from GitHub: {e}")
            return []

    # ========================================================================
    # DUCKDUCKGO SEARCH - Improved Web Scraping Fallback
    # ========================================================================

    def discover_from_ddg(
        self,
        industry: str,
        num_results: int = 20
    ) -> List[Dict]:
        """
        Free discovery using DuckDuckGo HTML endpoint with targeted queries
        """
        try:
            # Clean up the query string to prevent duplicate words
            clean_ind = re.sub(r'\b(companies|startups)\b', '', industry, flags=re.IGNORECASE).strip()
            
            # Formulate targeted queries that land on company homepages
            queries = [
                f'{clean_ind} "about us" site:.com',
                f'{clean_ind} "about us"',
                f'top {clean_ind} companies'
            ]
            
            companies = []
            seen_domains = set()
            
            ignored_domains = [
                'wikipedia.org', 'youtube.com', 'linkedin.com', 'facebook.com', 
                'twitter.com', 'github.com', 'reddit.com', 'medium.com', 
                'crunchbase.com', 'forbes.com', 'glassdoor.com', 'indeed.com',
                'bloomberg.com', 'quora.com', 'ycombinator.com', 'duckduckgo.com'
            ]

            url = "https://html.duckduckgo.com/html/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            for query in queries:
                if len(companies) >= num_results:
                    break
                    
                self.logger.info(f"Searching DuckDuckGo for query='{query}'")
                res = self.session.post(url, data={"q": query}, headers=headers, timeout=10)
                
                if res.status_code != 200:
                    continue
                    
                # Extract DuckDuckGo redirect URLs using Regex for max reliability
                raw_urls = re.findall(r'uddg=([^&"]+)', res.text)
                
                for encoded_url in raw_urls:
                    target_url = unquote(encoded_url)
                    
                    if not target_url.startswith('http'):
                        continue
                        
                    domain = urlparse(target_url).netloc.replace('www.', '').lower()
                    
                    if not domain or domain in seen_domains:
                        continue
                        
                    # Skip aggregator/directory/social media domains
                    if any(ignored in domain for ignored in ignored_domains):
                        continue
                        
                    seen_domains.add(domain)
                    comp_name = domain.split('.')[0].capitalize()
                    
                    companies.append({
                        'company_name': comp_name,
                        'website': f"https://{domain}",
                        'email': f"info@{domain}",
                        'industry': industry,
                        'discovery_source': 'duckduckgo'
                    })
                    
                    if len(companies) >= num_results:
                        break

            self.logger.info(f"✅ Found {len(companies)} companies from DuckDuckGo")
            return companies
            
        except Exception as e:
            self.logger.error(f"Error discovering from DuckDuckGo: {e}")
            return []

    # ========================================================================
    # COMBINED DISCOVERY
    # ========================================================================
    
    def discover_companies(
        self,
        industry: str,
        topic: str = None,
        location: str = None,
        num_results: int = 50
    ) -> List[Dict]:
        """
        Discover companies using multiple free sources
        """
        all_companies = []
        
        # 1. GitHub search if topic provided or sanitized from industry
        gh_topic = topic or re.sub(r'[^a-zA-Z0-9-]', '', industry.lower().replace(' ', '-'))
        github_companies = self.discover_from_github(
            topic=gh_topic,
            stars_min=5
        )
        all_companies.extend(github_companies)
        
        # 2. DuckDuckGo Search (Free fallback if needed)
        if len(all_companies) < num_results:
            search_query = f"{industry} {location}".strip() if location else industry
            ddg_companies = self.discover_from_ddg(
                industry=search_query,
                num_results=num_results - len(all_companies)
            )
            all_companies.extend(ddg_companies)
        
        # Deduplicate results by domain
        seen_websites = set()
        unique_companies = []
        
        for company in all_companies:
            website = company.get('website', '')
            if website and website not in seen_websites:
                seen_websites.add(website)
                unique_companies.append(company)
        
        self.logger.info(
            f"✅ Discovered {len(unique_companies)} unique companies"
        )
        
        return unique_companies[:num_results]


# Example usage
if __name__ == "__main__":
    discovery = CompanyDiscovery()
    
    companies = discovery.discover_companies(
        industry="Medical AI companies",
        location="US",
        num_results=5
    )
    
    for company in companies:
        print(f"- {company['company_name']}: {company.get('website', 'N/A')}")