# """
# ai_summarizer.py - AI Summarization
# ====================================
# Generate business summaries from website content using:
# - OpenRouter API
# - Google Gemma 4 model (free)
# - Fallback to NVIDIA Nemotron if needed

# Creates 2-3 sentence summaries of what companies do.
# """

# import requests
# import json
# from typing import Dict, Optional
# import time

# from .config import (
#     OPENROUTER_API_KEY,
#     OPENROUTER_API_URL,
#     OPENROUTER_MODEL_SUMMARY,
#     OPENROUTER_MODEL_SUMMARY_BACKUP,
#     SUMMARY_SYSTEM_PROMPT,
#     SUMMARY_PROMPT_TEMPLATE,
#     get_openrouter_headers,
# )
# from .error_handler import (
#     LoggerSetup,
#     ErrorTracker,
#     APIError,
# )

# # Setup logger
# logger = LoggerSetup.get_logger(__name__)
# error_tracker = ErrorTracker()


# class AISummarizer:
#     """
#     Generate business summaries using OpenRouter API
#     """
    
#     def __init__(self):
#         """Initialize AI summarizer"""
#         self.logger = logger
#         self.error_tracker = error_tracker
#         self.primary_model = OPENROUTER_MODEL_SUMMARY
#         self.backup_model = OPENROUTER_MODEL_SUMMARY_BACKUP
#         self.api_url = OPENROUTER_API_URL
#         self.headers = get_openrouter_headers()
        
#         self.logger.info(f"Initialized AI Summarizer")
#         self.logger.debug(f"Primary Model: {self.primary_model}")
#         self.logger.debug(f"Backup Model: {self.backup_model}")
    
#     # ========================================================================
#     # MAIN SUMMARIZATION METHOD
#     # ========================================================================
    
#     def summarize(self, lead: Dict) -> Dict:
#         """
#         Generate summary for a lead based on website content
        
#         Args:
#             lead (Dict): Lead data with website_content
        
#         Returns:
#             Dict: Lead with business_summary and summary_status added
#         """
#         try:
#             company_name = lead.get('company_name', '')
#             website_content = lead.get('website_content', '')
            
#             # Check if we have content to summarize
#             if not website_content or len(website_content) < 50:
#                 self.logger.debug(
#                     f"Skipping summarization for {company_name}: "
#                     f"Insufficient content"
#                 )
#                 lead['business_summary'] = ''
#                 lead['summary_status'] = 'skipped'
#                 return lead
            
#             self.logger.info(f"Summarizing: {company_name}")
            
#             # Call OpenRouter API
#             summary = self._call_openrouter(
#                 company_name,
#                 website_content,
#                 use_backup=False
#             )
            
#             if not summary:
#                 # Retry with backup model
#                 self.logger.debug(f"Retrying with backup model...")
#                 summary = self._call_openrouter(
#                     company_name,
#                     website_content,
#                     use_backup=True
#                 )
            
#             if summary:
#                 lead['business_summary'] = summary
#                 lead['summary_status'] = 'success'
#                 self.logger.info(
#                     f"✅ Summary generated for {company_name}"
#                 )
#                 return lead
#             else:
#                 raise APIError("Failed to generate summary from both models")
        
#         except APIError as e:
#             error_msg = str(e)
#             self.logger.warning(f"⚠️  API error for {company_name}: {error_msg}")
#             self.error_tracker.add_error(
#                 company_name,
#                 "APIError",
#                 error_msg,
#                 "ai_summarization"
#             )
#             lead['business_summary'] = ''
#             lead['summary_status'] = 'failed'
#             return lead
        
#         except Exception as e:
#             error_msg = f"Unexpected error: {str(e)}"
#             self.logger.error(f"❌ Error summarizing {company_name}: {error_msg}")
#             self.error_tracker.add_error(
#                 company_name,
#                 "APIError",
#                 error_msg,
#                 "ai_summarization"
#             )
#             lead['business_summary'] = ''
#             lead['summary_status'] = 'failed'
#             return lead
    
#     # ========================================================================
#     # OPENROUTER API CALL
#     # ========================================================================
    
#     def _call_openrouter(
#         self,
#         company_name: str,
#         website_content: str,
#         use_backup: bool = False
#     ) -> Optional[str]:
#         """
#         Call OpenRouter API to generate summary
        
#         Args:
#             company_name (str): Company name
#             website_content (str): Website text content
#             use_backup (bool): Use backup model if True
        
#         Returns:
#             str or None: Generated summary or None if failed
#         """
#         try:
#             # Select model
#             model = self.backup_model if use_backup else self.primary_model
#             self.logger.debug(f"Using model: {model}")
            
#             # Prepare prompt
#             prompt = SUMMARY_PROMPT_TEMPLATE.format(
#                 company_name=company_name,
#                 website_content=website_content[:2000]  # Limit context
#             )
            
#             # Prepare request payload
#             payload = {
#                 "model": model,
#                 "messages": [
#                     {
#                         "role": "system",
#                         "content": SUMMARY_SYSTEM_PROMPT
#                     },
#                     {
#                         "role": "user",
#                         "content": prompt
#                     }
#                 ],
#                 "temperature": 0.7,
#                 "max_tokens": 200,
#                 "top_p": 1,
#             }
            
#             self.logger.debug(f"Sending API request to OpenRouter...")
            
#             # Make request
#             response = requests.post(
#                 self.api_url,
#                 headers=self.headers,
#                 json=payload,
#                 timeout=30
#             )
            
#             # Check response
#             if response.status_code == 200:
#                 data = response.json()
                
#                 # Extract summary from response
#                 if 'choices' in data and len(data['choices']) > 0:
#                     choice_msg = data['choices'][0].get('message', {})
#                     raw_content = choice_msg.get('content') if isinstance(choice_msg, dict) else ''
#                     summary = (raw_content or '').strip()
                    
#                     # Validate summary
#                     if summary and len(summary) > 10:
#                         self.logger.debug(f"Summary generated: {len(summary)} chars")
#                         return summary
#                     else:
#                         raise APIError("Generated summary is empty or too short")
#                 else:
#                     raise APIError("Invalid response format from OpenRouter")
            
#             elif response.status_code == 401:
#                 raise APIError(
#                     "Authentication failed. Check OPENROUTER_API_KEY in .env"
#                 )
            
#             elif response.status_code == 429:
#                 raise APIError(
#                     "Rate limit exceeded. Wait before retrying. "
#                     "Consider adding $10 credits for 1000 daily requests."
#                 )
            
#             elif response.status_code == 400:
#                 error_data = response.json()
#                 error_msg = error_data.get('error', {}).get('message', 'Bad request')
#                 raise APIError(f"Bad request: {error_msg}")
            
#             else:
#                 raise APIError(
#                     f"API error (status {response.status_code}): "
#                     f"{response.text}"
#                 )
        
#         except requests.Timeout:
#             raise APIError("API request timeout (30 seconds)")
        
#         except requests.ConnectionError as e:
#             raise APIError(f"Connection error: {str(e)}")
        
#         except json.JSONDecodeError:
#             raise APIError("Failed to parse API response")
        
#         except APIError:
#             raise
        
#         except Exception as e:
#             raise APIError(f"Unexpected error: {str(e)}")
    
#     # ========================================================================
#     # BATCH PROCESSING
#     # ========================================================================
    
#     def summarize_batch(self, leads: list) -> list:
#         """
#         Generate summaries for a batch of leads
        
#         Args:
#             leads (list): List of lead dictionaries
        
#         Returns:
#             list: Leads with business_summary added
#         """
#         self.logger.info(f"Generating summaries for {len(leads)} leads...")
        
#         results = []
#         successful = 0
#         failed = 0
#         skipped = 0
        
#         for i, lead in enumerate(leads, 1):
#             result = self.summarize(lead)
#             results.append(result)
            
#             # Count
#             status = result.get('summary_status', 'unknown')
#             if status == 'success':
#                 successful += 1
#             elif status == 'failed':
#                 failed += 1
#             elif status == 'skipped':
#                 skipped += 1
            
#             # Log progress
#             if i % 5 == 0:
#                 self.logger.info(
#                     f"Progress: {i}/{len(leads)} - "
#                     f"Success: {successful}, Failed: {failed}, Skipped: {skipped}"
#                 )
            
#             # Rate limiting - be respectful to API
#             time.sleep(0.5)
        
#         self.logger.info(
#             f"✅ Summarization complete! "
#             f"Success: {successful}, Failed: {failed}, Skipped: {skipped}"
#         )
        
#         return results
    
#     # ========================================================================
#     # VALIDATION
#     # ========================================================================
    
#     def validate_api_key(self) -> bool:
#         """
#         Validate that API key is set and working
        
#         Returns:
#             bool: True if API key is valid
#         """
#         try:
#             if OPENROUTER_API_KEY == "not_set" or not OPENROUTER_API_KEY:
#                 self.logger.error("❌ OPENROUTER_API_KEY not set in .env")
#                 return False
            
#             self.logger.info("Validating OpenRouter API key...")
            
#             # Try a simple API call
#             payload = {
#                 "model": self.primary_model,
#                 "messages": [
#                     {
#                         "role": "user",
#                         "content": "Say 'Hello' in one word"
#                     }
#                 ],
#                 "max_tokens": 10,
#             }
            
#             response = requests.post(
#                 self.api_url,
#                 headers=self.headers,
#                 json=payload,
#                 timeout=10
#             )
            
#             if response.status_code == 200:
#                 self.logger.info("✅ API key is valid and working!")
#                 return True
#             else:
#                 error_data = response.json()
#                 error_msg = error_data.get('error', {}).get('message', 'Unknown error')
#                 self.logger.error(f"❌ API validation failed: {error_msg}")
#                 return False
        
#         except Exception as e:
#             self.logger.error(f"❌ API validation error: {e}")
#             return False
    
#     # ========================================================================
#     # RATE LIMIT INFO
#     # ========================================================================
    
#     def get_rate_limit_info(self) -> Dict:
#         """
#         Get information about API rate limits
        
#         Returns:
#             Dict: Rate limit information
#         """
#         return {
#             'free_tier_requests_per_day': 50,
#             'free_tier_with_credits': 1000,
#             'requests_per_minute': 20,
#             'model': self.primary_model,
#             'recommendation': 'Add $10 credits for 1000 daily requests'
#         }


# # ============================================================================
# # EXAMPLE USAGE
# # ============================================================================

# if __name__ == "__main__":
#     """
#     Test AI summarization
#     """
#     print("\n" + "="*60)
#     print("TESTING AI SUMMARIZER")
#     print("="*60 + "\n")
    
#     summarizer = AISummarizer()
    
#     # Test 1: Validate API key
#     print("Test 1: Validating API key...")
#     is_valid = summarizer.validate_api_key()
#     if not is_valid:
#         print("❌ API key validation failed. Check your .env file!")
#         print(f"   OPENROUTER_API_KEY should start with 'sk-or-v1-'")
#         exit(1)
    
#     # Test 2: Generate summaries
#     print("\nTest 2: Generating summaries for test leads...")
    
#     test_leads = [
#         {
#             'company_name': 'OpenAI',
#             'website_content': (
#                 'OpenAI is an AI research company focused on developing safe, '
#                 'beneficial artificial intelligence. We created ChatGPT, GPT-4, '
#                 'and other large language models. Our mission is to ensure AI benefits humanity.'
#             ),
#         },
#         {
#             'company_name': 'Company with no content',
#             'website_content': '',
#         },
#     ]
    
#     for lead in test_leads:
#         print(f"\n  Company: {lead['company_name']}")
#         result = summarizer.summarize(lead)
#         print(f"  Status: {result['summary_status']}")
#         if result['business_summary']:
#             print(f"  Summary: {result['business_summary']}")
    
#     # Test 3: Batch processing
#     print("\n" + "-"*60)
#     print("\nTest 3: Batch summarization")
#     results = summarizer.summarize_batch(test_leads)
#     print(f"\n✅ Processed {len(results)} leads")
    
#     # Show rate limit info
#     print("\n" + "-"*60)
#     print("\nRate Limit Information:")
#     rate_info = summarizer.get_rate_limit_info()
#     for key, value in rate_info.items():
#         print(f"  {key}: {value}")
    
#     # Show error report
#     error_summary = error_tracker.get_error_summary()
#     if error_summary:
#         print(f"\n⚠️  Errors: {error_summary['total_errors']}")
    
#     print("\n" + "="*60)
#     print("✅ AI summarizer test completed!")
#     print("="*60 + "\n")























"""
ai_summarizer.py - AI Summarization
====================================
Generate business summaries from website content using:
- Groq API
- Llama 3.3 70B Versatile model

Creates 2-3 sentence summaries of what companies do.
"""

import os
import json
from typing import Dict, Optional
import time
from dotenv import load_dotenv
from groq import Groq

from .config import (
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_PROMPT_TEMPLATE,
)
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    APIError,
)

# Load environment variables
load_dotenv()

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class AISummarizer:
    """
    Generate business summaries using Groq API
    """
    
    def __init__(self):
        """Initialize AI summarizer with Groq Client"""
        self.logger = logger
        self.error_tracker = error_tracker
        self.primary_model = "llama-3.3-70b-versatile"
        self.backup_model = "llama-3.1-8b-instant"
        self.api_key = os.getenv("GROQ_API_KEY", "")
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
        
        self.logger.info(f"Initialized AI Summarizer (Groq API)")
        self.logger.debug(f"Primary Model: {self.primary_model}")
        self.logger.debug(f"Backup Model: {self.backup_model}")
    
    # ========================================================================
    # MAIN SUMMARIZATION METHOD
    # ========================================================================
    
    def summarize(self, lead: Dict) -> Dict:
        """
        Generate summary for a lead based on website content
        
        Args:
            lead (Dict): Lead data with website_content
        
        Returns:
            Dict: Lead with business_summary and summary_status added
        """
        try:
            company_name = lead.get('company_name', '')
            website_content = lead.get('website_content', '')
            
            # Check if we have content to summarize
            if not website_content or len(website_content) < 50:
                self.logger.debug(
                    f"Skipping summarization for {company_name}: "
                    f"Insufficient content"
                )
                lead['business_summary'] = ''
                lead['summary_status'] = 'skipped'
                return lead
            
            self.logger.info(f"Summarizing: {company_name}")
            
            # Call Groq API
            summary = self._call_openrouter(
                company_name,
                website_content,
                use_backup=False
            )
            
            if not summary:
                # Retry with backup model
                self.logger.debug(f"Retrying with backup model...")
                summary = self._call_openrouter(
                    company_name,
                    website_content,
                    use_backup=True
                )
            
            if summary:
                lead['business_summary'] = summary
                lead['summary_status'] = 'success'
                self.logger.info(
                    f"✅ Summary generated for {company_name}"
                )
                return lead
            else:
                raise APIError("Failed to generate summary from both models")
        
        except APIError as e:
            error_msg = str(e)
            self.logger.warning(f"⚠️  API error for {company_name}: {error_msg}")
            self.error_tracker.add_error(
                company_name,
                "APIError",
                error_msg,
                "ai_summarization"
            )
            lead['business_summary'] = ''
            lead['summary_status'] = 'failed'
            return lead
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"❌ Error summarizing {company_name}: {error_msg}")
            self.error_tracker.add_error(
                company_name,
                "APIError",
                error_msg,
                "ai_summarization"
            )
            lead['business_summary'] = ''
            lead['summary_status'] = 'failed'
            return lead
    
    # ========================================================================
    # GROQ API CALL (Replaces OpenRouter Call)
    # ========================================================================
    
    def _call_openrouter(
        self,
        company_name: str,
        website_content: str,
        use_backup: bool = False
    ) -> Optional[str]:
        """
        Call Groq API to generate summary
        
        Args:
            company_name (str): Company name
            website_content (str): Website text content
            use_backup (bool): Use backup model if True
        
        Returns:
            str or None: Generated summary or None if failed
        """
        try:
            if not self.client:
                raise APIError("GROQ_API_KEY is not set in environment or .env file.")

            # Select model
            model = self.backup_model if use_backup else self.primary_model
            self.logger.debug(f"Using model: {model}")
            
            # Prepare prompt
            prompt = SUMMARY_PROMPT_TEMPLATE.format(
                company_name=company_name,
                website_content=website_content[:3000]  # Safe token ceiling
            )
            
            self.logger.debug(f"Sending API request to Groq...")
            
            # Make request via Groq SDK
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": SUMMARY_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=250,
                top_p=1,
            )
            
            if response and response.choices and len(response.choices) > 0:
                choice_msg = response.choices[0].message
                summary = (choice_msg.content or '').strip() if choice_msg else ''
                
                # Validate summary
                if summary and len(summary) > 10:
                    self.logger.debug(f"Summary generated: {len(summary)} chars")
                    return summary
                else:
                    raise APIError("Generated summary is empty or too short")
            else:
                raise APIError("Invalid or empty response format from Groq API")

        except APIError:
            raise

        except Exception as e:
            raise APIError(f"Groq API call failed: {str(e)}")
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def summarize_batch(self, leads: list) -> list:
        """
        Generate summaries for a batch of leads
        
        Args:
            leads (list): List of lead dictionaries
        
        Returns:
            list: Leads with business_summary added
        """
        self.logger.info(f"Generating summaries for {len(leads)} leads...")
        
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        for i, lead in enumerate(leads, 1):
            result = self.summarize(lead)
            results.append(result)
            
            # Count
            status = result.get('summary_status', 'unknown')
            if status == 'success':
                successful += 1
            elif status == 'failed':
                failed += 1
            elif status == 'skipped':
                skipped += 1
            
            # Log progress
            if i % 5 == 0:
                self.logger.info(
                    f"Progress: {i}/{len(leads)} - "
                    f"Success: {successful}, Failed: {failed}, Skipped: {skipped}"
                )
            
            # Rate limiting - respectful delay
            time.sleep(0.2)
        
        self.logger.info(
            f"✅ Summarization complete! "
            f"Success: {successful}, Failed: {failed}, Skipped: {skipped}"
        )
        
        return results
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate_api_key(self) -> bool:
        """
        Validate that API key is set and working
        
        Returns:
            bool: True if API key is valid
        """
        try:
            if not self.api_key or self.api_key == "not_set":
                self.logger.error("❌ GROQ_API_KEY not set in .env")
                return False
            
            self.logger.info("Validating Groq API key...")
            
            if not self.client:
                self.client = Groq(api_key=self.api_key)

            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[
                    {
                        "role": "user",
                        "content": "Say 'Hello' in one word"
                    }
                ],
                max_tokens=10,
            )
            
            if response and response.choices:
                self.logger.info("✅ Groq API key is valid and working!")
                return True
            else:
                self.logger.error("❌ API validation failed: Empty choices returned")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ API validation error: {e}")
            return False
    
    # ========================================================================
    # RATE LIMIT INFO
    # ========================================================================
    
    def get_rate_limit_info(self) -> Dict:
        """
        Get information about API rate limits
        
        Returns:
            Dict: Rate limit information
        """
        return {
            'free_tier_requests_per_day': 14400,
            'requests_per_minute': 30,
            'model': self.primary_model,
            'provider': 'Groq Cloud'
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test AI summarization
    """
    print("\n" + "="*60)
    print("TESTING AI SUMMARIZER (GROQ ENGINE)")
    print("="*60 + "\n")
    
    summarizer = AISummarizer()
    
    # Test 1: Validate API key
    print("Test 1: Validating API key...")
    is_valid = summarizer.validate_api_key()
    if not is_valid:
        print("❌ API key validation failed. Check your .env file for GROQ_API_KEY!")
        exit(1)
    
    # Test 2: Generate summaries
    print("\nTest 2: Generating summaries for test leads...")
    
    test_leads = [
        {
            'company_name': 'OpenAI',
            'website_content': (
                'OpenAI is an AI research company focused on developing safe, '
                'beneficial artificial intelligence. We created ChatGPT, GPT-4, '
                'and other large language models. Our mission is to ensure AI benefits humanity.'
            ),
        },
        {
            'company_name': 'Company with no content',
            'website_content': '',
        },
    ]
    
    for lead in test_leads:
        print(f"\n  Company: {lead['company_name']}")
        result = summarizer.summarize(lead)
        print(f"  Status: {result['summary_status']}")
        if result['business_summary']:
            print(f"  Summary: {result['business_summary']}")
    
    # Test 3: Batch processing
    print("\n" + "-"*60)
    print("\nTest 3: Batch summarization")
    results = summarizer.summarize_batch(test_leads)
    print(f"\n✅ Processed {len(results)} leads")
    
    # Show rate limit info
    print("\n" + "-"*60)
    print("\nRate Limit Information:")
    rate_info = summarizer.get_rate_limit_info()
    for key, value in rate_info.items():
        print(f"  {key}: {value}")
    
    # Show error report
    error_summary = error_tracker.get_error_summary()
    if error_summary:
        print(f"\n⚠️  Errors: {error_summary['total_errors']}")
    
    print("\n" + "="*60)
    print("✅ AI summarizer test completed!")
    print("="*60 + "\n")