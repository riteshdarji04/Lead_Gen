"""
lead_discovery.py - Automatic Lead Discovery (Scenario 2)
==========================================================
When you DON'T have a list of companies, this module finds them for you.

You provide:
  - Industry / niche  (e.g. "Healthcare AI startups")
  - Location          (e.g. "USA", "New York")
  - Company size      (e.g. "10-100 employees")
  - Number of leads   (e.g. 50)

What it does:
  1. Calls the Apify REST API to run a company-scraping actor
  2. Waits for the run to finish (polling)
  3. Fetches results and normalises them into the standard lead format
  4. Returns List[Dict] ready to feed into the main pipeline

Dependencies:
  - requests (already in requirements.txt)
  - APIFY_API_TOKEN set in .env  (optional — disables if missing)

Apify actor used by default: compass/crawler-google-places
  (searches Google Maps for businesses matching your query)
"""

import time
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse

from .config import (
    APIPY_API_TOKEN,
    APIPY_ACTOR_ID,
    APIPY_BASE_URL,
    APIPY_RUN_TIMEOUT,
)
from .error_handler import LoggerSetup, ErrorTracker

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class LeadDiscovery:
    """
    Automatic lead discovery using Apify actors.

    Scenario 2: User provides industry/criteria -> system finds companies.
    """

    def __init__(self):
        self.logger = logger
        self.error_tracker = error_tracker
        self._apify_available = APIPY_API_TOKEN != "not_set"

        if not self._apify_available:
            self.logger.warning(
                "APIFY_API_TOKEN not set. "
                "Scenario 2 (auto discovery) is DISABLED. "
                "Add APIFY_API_TOKEN to your .env file to enable it."
            )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def discover_leads(
        self,
        industry: str,
        location: str = "USA",
        company_size: str = "",
        num_leads: int = 50,
    ) -> List[Dict]:
        """
        Discover companies matching the given criteria.

        Args:
            industry (str):      Industry/niche to search (e.g. "Healthcare AI")
            location (str):      Location filter        (e.g. "New York, USA")
            company_size (str):  Employee range hint    (e.g. "10-100 employees")
            num_leads (int):     Max number of leads to return

        Returns:
            List[Dict]: Leads in standard format (company_name, email, website, industry)
        """
        if not self._apify_available:
            self.logger.error(
                "Cannot run auto discovery: APIFY_API_TOKEN not set in .env"
            )
            print(
                "\n Scenario 2 requires an Apify API token.\n"
                "   1. Sign up free at https://apify.com\n"
                "   2. Get your token from https://console.apify.com/account/integrations\n"
                "   3. Add APIFY_API_TOKEN=<your_token> to your .env file\n"
                "   4. Re-run with --source auto\n"
            )
            return []

        self.logger.info(
            f"Discovering leads: industry='{industry}', "
            f"location='{location}', size='{company_size}', count={num_leads}"
        )

        # Build search query for the Apify actor
        search_query = self._build_search_query(industry, location, company_size)

        # Trigger the Apify actor run
        run_id = self._start_actor_run(search_query, num_leads)
        if not run_id:
            return []

        # Wait for completion
        success = self._wait_for_run(run_id)
        if not success:
            return []

        # Fetch and normalise results
        raw_results = self._fetch_results(run_id, num_leads)
        leads = self._normalise_results(raw_results, industry)

        self.logger.info(f"Discovered {len(leads)} leads for '{industry}'")
        return leads

    # ========================================================================
    # APIFY ACTOR INTERACTION
    # ========================================================================

    def _build_search_query(
        self, industry: str, location: str, company_size: str
    ) -> str:
        """Build a search string for the Apify actor."""
        query = industry.strip()
        if location.strip():
            query += f" in {location.strip()}"
        return query

    def _start_actor_run(self, search_query: str, max_results: int) -> Optional[str]:
        """
        Start an Apify actor run via the REST API.

        Returns:
            str: Run ID if successful, None if failed
        """
        url = f"{APIPY_BASE_URL}/acts/{APIPY_ACTOR_ID}/runs"

        # Input payload for compass/crawler-google-places
        payload = {
            "searchStringsArray": [search_query],
            "maxCrawledPlacesPerSearch": max_results,
            "language": "en",
            "maxImages": 0,
            "exportPlaceUrls": False,
            "includeHistogram": False,
            "includeOpeningHours": False,
            "includePeopleAlsoSearch": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {APIPY_API_TOKEN}",
        }

        try:
            self.logger.info(f"Starting Apify actor run for: '{search_query}'")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            run_id = data.get("data", {}).get("id")

            if run_id:
                self.logger.info(f"Apify run started: {run_id}")
                print(
                    f"   Apify actor running (ID: {run_id}) "
                    "-- this may take a minute..."
                )
                return run_id
            else:
                self.logger.error(f"No run ID in Apify response: {data}")
                return None

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                self.logger.error(
                    "Apify authentication failed -- check your APIFY_API_TOKEN"
                )
            else:
                self.logger.error(f"Apify API error: {e}")
            return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to start Apify run: {e}")
            return None

    def _wait_for_run(self, run_id: str) -> bool:
        """
        Poll the Apify run status until it finishes or times out.

        Returns:
            bool: True if run SUCCEEDED, False otherwise
        """
        url = f"{APIPY_BASE_URL}/actor-runs/{run_id}"
        headers = {"Authorization": f"Bearer {APIPY_API_TOKEN}"}

        start = time.time()
        poll_interval = 5  # seconds

        while True:
            elapsed = time.time() - start

            if elapsed > APIPY_RUN_TIMEOUT:
                self.logger.error(
                    f"Apify run timed out after {APIPY_RUN_TIMEOUT}s "
                    f"(run ID: {run_id})"
                )
                return False

            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()

                status = data.get("data", {}).get("status", "UNKNOWN")

                if status == "SUCCEEDED":
                    self.logger.info(f"Apify run SUCCEEDED in {elapsed:.0f}s")
                    return True

                elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    self.logger.error(f"Apify run ended with status: {status}")
                    return False

                else:
                    # RUNNING or READY -- keep waiting
                    print(
                        f"   Apify run status: {status} ({elapsed:.0f}s elapsed)...",
                        end="\r",
                        flush=True,
                    )
                    time.sleep(poll_interval)

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Error polling Apify run status: {e}")
                time.sleep(poll_interval)

    def _fetch_results(self, run_id: str, limit: int) -> List[Dict]:
        """
        Fetch the raw results from the completed Apify run dataset.

        Returns:
            List[Dict]: Raw results from the actor
        """
        url = f"{APIPY_BASE_URL}/actor-runs/{run_id}/dataset/items"
        headers = {"Authorization": f"Bearer {APIPY_API_TOKEN}"}
        params = {"limit": limit, "format": "json"}

        try:
            self.logger.info("Fetching results from Apify dataset...")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            items = response.json()
            self.logger.info(f"Fetched {len(items)} raw results from Apify")
            return items

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch Apify results: {e}")
            return []

    # ========================================================================
    # DATA NORMALISATION
    # ========================================================================

    def _normalise_results(
        self, raw_results: List[Dict], industry: str
    ) -> List[Dict]:
        """
        Convert Apify actor output into the standard lead format.

        The compass/crawler-google-places actor returns fields like:
            - title        -> company_name
            - website      -> website
            - phone        -> (ignored for now)
            - categoryName -> industry hint

        Returns:
            List[Dict]: Normalised leads
        """
        leads = []

        for item in raw_results:
            company_name = (
                item.get("title")
                or item.get("name")
                or item.get("company_name")
                or ""
            ).strip()

            if not company_name:
                continue

            website = (
                item.get("website")
                or item.get("url")
                or ""
            ).strip()

            # Apify doesn't always return emails from Google Maps;
            # derive a best-guess email from domain if website is available
            email = item.get("email", "").strip()
            if not email and website:
                domain = self._extract_domain(website)
                if domain:
                    email = f"contact@{domain}"

            # Use actor's category or fall back to user-provided industry
            detected_industry = (
                item.get("categoryName")
                or item.get("category")
                or industry
            ).strip()

            # Must have at least a name and one contact point
            if not company_name or (not email and not website):
                continue

            leads.append({
                "company_name": company_name,
                "email": email,
                "website": website,
                "industry": detected_industry,
            })

        return leads

    def _extract_domain(self, url: str) -> str:
        """Extract bare domain from a URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Strip www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    # ========================================================================
    # UTILITY
    # ========================================================================

    def is_available(self) -> bool:
        """Check if Apify discovery is available (token configured)."""
        return self._apify_available

    def get_actor_info(self) -> Dict:
        """Return info about the configured actor."""
        return {
            "actor_id": APIPY_ACTOR_ID,
            "apify_available": self._apify_available,
            "base_url": APIPY_BASE_URL,
            "timeout": APIPY_RUN_TIMEOUT,
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test lead discovery (Scenario 2)
    """
    print("\n" + "="*60)
    print("TESTING LEAD DISCOVERY (SCENARIO 2)")
    print("="*60 + "\n")

    discovery = LeadDiscovery()

    if not discovery.is_available():
        print("Apify not configured. Add APIFY_API_TOKEN to .env to test.")
    else:
        print("Discovering Healthcare AI leads in USA...")
        leads = discovery.discover_leads(
            industry="Healthcare AI startups",
            location="USA",
            company_size="10-100 employees",
            num_leads=5,
        )

        print(f"\nFound {len(leads)} leads:\n")
        for lead in leads:
            print(f"  - {lead['company_name']}")
            print(f"    Email:    {lead['email']}")
            print(f"    Website:  {lead['website']}")
            print(f"    Industry: {lead['industry']}\n")

    print("="*60 + "\n")
