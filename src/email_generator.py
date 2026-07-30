# """
# email_generator.py - Email Generation
# ======================================
# Generate personalized B2B outreach emails using:
# - OpenRouter API
# - Tencent Hy3 model (free)
# - HTML formatting with inline CSS
# - Professional templates with CTA buttons

# Creates personalized emails based on company business summaries.
# """

# import requests
# import json
# from typing import Dict, Optional
# import time

# from .config import (
#     OPENROUTER_API_KEY,
#     OPENROUTER_API_URL,
#     OPENROUTER_MODEL_EMAIL,
#     OPENROUTER_MODEL_EMAIL_BACKUP,
#     EMAIL_SYSTEM_PROMPT,
#     EMAIL_PROMPT_TEMPLATE,
#     get_openrouter_headers,
# )
# from .error_handler import (
#     LoggerSetup,
#     ErrorTracker,
#     APIError,
#     EmailGenerationError,
# )

# # Setup logger
# logger = LoggerSetup.get_logger(__name__)
# error_tracker = ErrorTracker()


# class EmailGenerator:
#     """
#     Generate personalized outreach emails using OpenRouter API
#     """
    
#     def __init__(self):
#         """Initialize email generator"""
#         self.logger = logger
#         self.error_tracker = error_tracker
#         self.primary_model = OPENROUTER_MODEL_EMAIL
#         self.backup_model = OPENROUTER_MODEL_EMAIL_BACKUP
#         self.api_url = OPENROUTER_API_URL
#         self.headers = get_openrouter_headers()
        
#         self.logger.info(f"Initialized Email Generator")
#         self.logger.debug(f"Primary Model: {self.primary_model}")
#         self.logger.debug(f"Backup Model: {self.backup_model}")
    
#     # ========================================================================
#     # MAIN EMAIL GENERATION METHOD
#     # ========================================================================
    
#     def generate_email(self, lead: Dict) -> Dict:
#         """
#         Generate personalized email for a lead
        
#         Args:
#             lead (Dict): Lead data with company info and business summary
        
#         Returns:
#             Dict: Lead with generated_email and email_status added
#         """
#         try:
#             company_name = lead.get('company_name', '')
#             business_summary = lead.get('business_summary', '')
#             industry = lead.get('industry', '')
            
#             # Check if we have required data
#             if not company_name:
#                 raise EmailGenerationError("Company name is required")
            
#             if not business_summary or len(business_summary) < 20:
#                 self.logger.debug(
#                     f"Skipping email for {company_name}: "
#                     f"No business summary available"
#                 )
#                 lead['generated_email'] = ''
#                 lead['email_status'] = 'skipped'
#                 return lead
            
#             self.logger.info(f"Generating email for: {company_name}")
            
#             # Call OpenRouter API
#             email_html = self._call_openrouter(
#                 company_name,
#                 business_summary,
#                 industry,
#                 use_backup=False
#             )
            
#             if not email_html:
#                 # Retry with backup model
#                 self.logger.debug(f"Retrying with backup model...")
#                 email_html = self._call_openrouter(
#                     company_name,
#                     business_summary,
#                     industry,
#                     use_backup=True
#                 )
            
#             if email_html:
#                 # Ensure it's valid HTML
#                 if not email_html.strip().startswith('<'):
#                     email_html = self._wrap_in_html(email_html)
                
#                 lead['generated_email'] = email_html
#                 lead['email_status'] = 'success'
#                 self.logger.info(
#                     f"✅ Email generated for {company_name}"
#                 )
#                 return lead
#             else:
#                 raise APIError("Failed to generate email from both models")
        
#         except EmailGenerationError as e:
#             error_msg = str(e)
#             self.logger.warning(f"⚠️  Error for {company_name}: {error_msg}")
#             self.error_tracker.add_error(
#                 company_name,
#                 "EmailGenerationError",
#                 error_msg,
#                 "email_generation"
#             )
#             lead['generated_email'] = ''
#             lead['email_status'] = 'failed'
#             return lead
        
#         except APIError as e:
#             error_msg = str(e)
#             self.logger.warning(f"⚠️  API error for {company_name}: {error_msg}")
#             self.error_tracker.add_error(
#                 company_name,
#                 "APIError",
#                 error_msg,
#                 "email_generation"
#             )
#             lead['generated_email'] = ''
#             lead['email_status'] = 'failed'
#             return lead
        
#         except Exception as e:
#             error_msg = f"Unexpected error: {str(e)}"
#             self.logger.error(f"❌ Error generating email: {error_msg}")
#             self.error_tracker.add_error(
#                 company_name,
#                 "EmailGenerationError",
#                 error_msg,
#                 "email_generation"
#             )
#             lead['generated_email'] = ''
#             lead['email_status'] = 'failed'
#             return lead
    
#     # ========================================================================
#     # OPENROUTER API CALL
#     # ========================================================================
    
#     def _call_openrouter(
#         self,
#         company_name: str,
#         business_summary: str,
#         industry: str,
#         use_backup: bool = False
#     ) -> Optional[str]:
#         """
#         Call OpenRouter API to generate email
        
#         Args:
#             company_name (str): Company name
#             business_summary (str): Business summary
#             industry (str): Industry
#             use_backup (bool): Use backup model if True
        
#         Returns:
#             str or None: Generated email HTML or None if failed
#         """
#         try:
#             # Select model
#             model = self.backup_model if use_backup else self.primary_model
#             self.logger.debug(f"Using model: {model}")
            
#             # Prepare prompt
#             prompt = EMAIL_PROMPT_TEMPLATE.format(
#                 company_name=company_name,
#                 industry=industry if industry else "Not specified",
#                 company_size="Not specified",
#                 business_summary=business_summary
#             )
            
#             # Prepare request payload
#             payload = {
#                 "model": model,
#                 "messages": [
#                     {
#                         "role": "system",
#                         "content": EMAIL_SYSTEM_PROMPT
#                     },
#                     {
#                         "role": "user",
#                         "content": prompt
#                     }
#                 ],
#                 "temperature": 0.8,  # Slightly higher for more creativity
#                 "max_tokens": 500,
#                 "top_p": 1,
#             }
            
#             self.logger.debug(f"Sending email generation request to OpenRouter...")
            
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
                
#                 # Extract email from response
#                 if 'choices' in data and len(data['choices']) > 0:
#                     email_content = data['choices'][0]['message']['content']
#                     if not email_content:
#                         raise APIError("Empty response from API")
#                     choice_msg = data['choices'][0].get('message', {})
#                     raw_content = choice_msg.get('content') if isinstance(choice_msg, dict) else ''
#                     email = (raw_content or '').strip()
                    
#                     # Remove markdown code blocks if present
#                     if email.startswith('```'):
#                         email = email.split('```')[1]
#                         if email.startswith('html'):
#                             email = email[4:]
#                         email = email.strip()
                    
#                     # Validate email
#                     if email and len(email) > 15:
#                         self.logger.debug(f"Email generated: {len(email)} chars")
#                         return email
#                     else:
#                         raise APIError("Generated email is empty or too short")
#                 else:
#                     raise APIError("Invalid response format from OpenRouter")
            
#             elif response.status_code == 401:
#                 raise APIError(
#                     "Authentication failed. Check OPENROUTER_API_KEY in .env"
#                 )
            
#             elif response.status_code == 429:
#                 raise APIError(
#                     "Rate limit exceeded. Wait before retrying. "
#                     "Add $10 credits for 1000 daily requests."
#                 )
            
#             elif response.status_code == 400:
#                 error_data = response.json()
#                 error_msg = error_data.get('error', {}).get('message', 'Bad request')
#                 raise APIError(f"Bad request: {error_msg}")
            
#             else:
#                 raise APIError(
#                     f"API error (status {response.status_code}): "
#                     f"{response.text[:200]}"
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
#     # HTML WRAPPING
#     # ========================================================================
    
#     def _wrap_in_html(self, text: str) -> str:
#         """
#         Wrap plain text in HTML email template
        
#         Args:
#             text (str): Plain text email
        
#         Returns:
#             str: HTML wrapped email
#         """
#         html_template = """<html>
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
# </head>
# <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
#     {text}
# </body>
# </html>"""
        
#         return html_template.format(text=text)
    
#     # ========================================================================
#     # BATCH PROCESSING
#     # ========================================================================
    
#     def generate_emails_batch(self, leads: list) -> list:
#         """
#         Generate emails for a batch of leads
        
#         Args:
#             leads (list): List of lead dictionaries
        
#         Returns:
#             list: Leads with generated_email added
#         """
#         self.logger.info(f"Generating emails for {len(leads)} leads...")
        
#         results = []
#         successful = 0
#         failed = 0
#         skipped = 0
        
#         for i, lead in enumerate(leads, 1):
#             result = self.generate_email(lead)
#             results.append(result)
            
#             # Count
#             status = result.get('email_status', 'unknown')
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
            
#             # Rate limiting
#             time.sleep(0.5)
        
#         self.logger.info(
#             f"✅ Email generation complete! "
#             f"Success: {successful}, Failed: {failed}, Skipped: {skipped}"
#         )
        
#         return results
    
#     # ========================================================================
#     # EMAIL PREVIEW
#     # ========================================================================
    
#     def get_email_preview(self, email_html: str, length: int = 200) -> str:
#         """
#         Get a text preview of generated email
        
#         Args:
#             email_html (str): HTML email content
#             length (int): Preview length in characters
        
#         Returns:
#             str: Text preview
#         """
#         # Remove HTML tags
#         import re
#         text = re.sub('<[^<]+?>', '', email_html)
#         return text[:length]
    
#     # ========================================================================
#     # VALIDATION
#     # ========================================================================
    
#     def is_valid_email_html(self, email_html: str) -> bool:
#         """
#         Validate generated email HTML
        
#         Args:
#             email_html (str): Email HTML content
        
#         Returns:
#             bool: True if valid
#         """
#         if not email_html:
#             return False
        
#         # Must have minimum content
#         if len(email_html) < 100:
#             return False
        
#         # Should contain HTML or basic text
#         has_structure = any([
#             '<' in email_html,  # Has HTML tags
#             '\n' in email_html,  # Has line breaks
#             len(email_html.split()) > 20  # Has enough words
#         ])
        
#         return has_structure


# # ============================================================================
# # EXAMPLE USAGE
# # ============================================================================

# if __name__ == "__main__":
#     """
#     Test email generation
#     """
#     print("\n" + "="*60)
#     print("TESTING EMAIL GENERATOR")
#     print("="*60 + "\n")
    
#     generator = EmailGenerator()
    
#     # Test 1: Generate single email
#     print("Test 1: Generating personalized email...")
    
#     test_lead = {
#         'company_name': 'OpenAI',
#         'business_summary': (
#             'OpenAI is an AI research company that develops advanced language models '
#             'and AI systems. They create tools like ChatGPT and GPT-4 that help '
#             'businesses and developers build AI-powered applications.'
#         ),
#         'industry': 'AI & Technology',
#     }
    
#     result = generator.generate_email(test_lead)
    
#     print(f"\n  Company: {result['company_name']}")
#     print(f"  Status: {result['email_status']}")
    
#     if result['generated_email']:
#         preview = generator.get_email_preview(result['generated_email'], 300)
#         print(f"\n  Email Preview:")
#         print(f"  {preview}...")
    
#     # Test 2: Batch processing
#     print("\n" + "-"*60)
#     print("\nTest 2: Batch email generation")
    
#     test_leads = [
#         {
#             'company_name': 'OpenAI',
#             'business_summary': (
#                 'OpenAI develops advanced AI language models and systems. '
#                 'They create ChatGPT and GPT-4 for business applications.'
#             ),
#             'industry': 'AI',
#         },
#         {
#             'company_name': 'Company with no summary',
#             'business_summary': '',
#             'industry': 'Tech',
#         },
#     ]
    
#     results = generator.generate_emails_batch(test_leads)
#     print(f"\n✅ Generated emails for {len(results)} leads")
    
#     # Count results
#     successful = sum(1 for r in results if r.get('email_status') == 'success')
#     print(f"   Successful: {successful}")
    
#     # Show error report
#     error_summary = error_tracker.get_error_summary()
#     if error_summary:
#         print(f"\n⚠️  Errors: {error_summary['total_errors']}")
    
#     print("\n" + "="*60)
#     print("✅ Email generator test completed!")
#     print("="*60 + "\n")






























"""
email_generator.py - Email Generation
======================================
Generate personalized B2B outreach emails using:
- Groq API
- Llama 3.3 70B Versatile model
- HTML formatting with inline CSS
- Professional templates with CTA buttons

Creates personalized emails based on company business summaries.
"""

import os
import json
import re
from typing import Dict, Optional
import time
from dotenv import load_dotenv
from groq import Groq

from .config import (
    EMAIL_SYSTEM_PROMPT,
    EMAIL_PROMPT_TEMPLATE,
)
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    APIError,
    EmailGenerationError,
)

# Load environment variables
load_dotenv()

# Setup logger
logger = LoggerSetup.get_logger(__name__)
error_tracker = ErrorTracker()


class EmailGenerator:
    """
    Generate personalized outreach emails using Groq API
    """
    
    def __init__(self):
        """Initialize email generator with Groq Client"""
        self.logger = logger
        self.error_tracker = error_tracker
        self.primary_model = "llama-3.3-70b-versatile"
        self.backup_model = "llama-3.1-8b-instant"
        self.api_key = os.getenv("GROQ_API_KEY", "")
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
        
        self.logger.info(f"Initialized Email Generator (Groq API)")
        self.logger.debug(f"Primary Model: {self.primary_model}")
        self.logger.debug(f"Backup Model: {self.backup_model}")
    
    # ========================================================================
    # MAIN EMAIL GENERATION METHOD
    # ========================================================================
    
    def generate_email(self, lead: Dict) -> Dict:
        """
        Generate personalized email for a lead
        
        Args:
            lead (Dict): Lead data with company info and business summary
        
        Returns:
            Dict: Lead with generated_email and email_status added
        """
        try:
            company_name = lead.get('company_name', '')
            business_summary = lead.get('business_summary', '')
            industry = lead.get('industry', '')
            
            # Check if we have required data
            if not company_name:
                raise EmailGenerationError("Company name is required")
            
            if not business_summary or len(business_summary) < 20:
                self.logger.debug(
                    f"Skipping email for {company_name}: "
                    f"No business summary available"
                )
                lead['generated_email'] = ''
                lead['email_status'] = 'skipped'
                return lead
            
            self.logger.info(f"Generating email for: {company_name}")
            
            # Call Groq API
            email_html = self._call_openrouter(
                company_name,
                business_summary,
                industry,
                use_backup=False
            )
            
            if not email_html:
                # Retry with backup model
                self.logger.debug(f"Retrying with backup model...")
                email_html = self._call_openrouter(
                    company_name,
                    business_summary,
                    industry,
                    use_backup=True
                )
            
            if email_html:
                # Ensure it's valid HTML
                if not email_html.strip().startswith('<'):
                    email_html = self._wrap_in_html(email_html)
                
                lead['generated_email'] = email_html
                lead['email_status'] = 'success'
                self.logger.info(
                    f"✅ Email generated for {company_name}"
                )
                return lead
            else:
                raise APIError("Failed to generate email from both models")
        
        except EmailGenerationError as e:
            error_msg = str(e)
            self.logger.warning(f"⚠️  Error for {company_name}: {error_msg}")
            self.error_tracker.add_error(
                company_name,
                "EmailGenerationError",
                error_msg,
                "email_generation"
            )
            lead['generated_email'] = ''
            lead['email_status'] = 'failed'
            return lead
        
        except APIError as e:
            error_msg = str(e)
            self.logger.warning(f"⚠️  API error for {company_name}: {error_msg}")
            self.error_tracker.add_error(
                company_name,
                "APIError",
                error_msg,
                "email_generation"
            )
            lead['generated_email'] = ''
            lead['email_status'] = 'failed'
            return lead
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"❌ Error generating email: {error_msg}")
            self.error_tracker.add_error(
                company_name,
                "EmailGenerationError",
                error_msg,
                "email_generation"
            )
            lead['generated_email'] = ''
            lead['email_status'] = 'failed'
            return lead
    
    # ========================================================================
    # GROQ API CALL (Replaces OpenRouter Call)
    # ========================================================================
    
    def _call_openrouter(
        self,
        company_name: str,
        business_summary: str,
        industry: str,
        use_backup: bool = False
    ) -> Optional[str]:
        """
        Call Groq API to generate email
        
        Args:
            company_name (str): Company name
            business_summary (str): Business summary
            industry (str): Industry
            use_backup (bool): Use backup model if True
        
        Returns:
            str or None: Generated email HTML or None if failed
        """
        try:
            if not self.client:
                raise APIError("GROQ_API_KEY is not set in environment or .env file.")

            # Select model
            model = self.backup_model if use_backup else self.primary_model
            self.logger.debug(f"Using model: {model}")
            
            # Prepare prompt
            prompt = EMAIL_PROMPT_TEMPLATE.format(
                company_name=company_name,
                industry=industry if industry else "Not specified",
                company_size="Not specified",
                business_summary=business_summary
            )
            
            self.logger.debug(f"Sending email generation request to Groq...")
            
            # Make request via Groq SDK
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": EMAIL_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=600,
                top_p=1,
            )
            
            if response and response.choices and len(response.choices) > 0:
                choice_msg = response.choices[0].message
                raw_content = choice_msg.content if choice_msg else ''
                email = (raw_content or '').strip()
                
                # Remove markdown code blocks if present
                if email.startswith('```'):
                    parts = email.split('```')
                    if len(parts) > 1:
                        email = parts[1]
                        if email.startswith('html'):
                            email = email[4:]
                        email = email.strip()
                
                # Validate email
                if email and len(email) > 15:
                    self.logger.debug(f"Email generated: {len(email)} chars")
                    return email
                else:
                    raise APIError("Generated email is empty or too short")
            else:
                raise APIError("Invalid or empty response format from Groq API")

        except APIError:
            raise

        except Exception as e:
            raise APIError(f"Groq API call failed: {str(e)}")
    
    # ========================================================================
    # HTML WRAPPING
    # ========================================================================
    
    def _wrap_in_html(self, text: str) -> str:
        """
        Wrap plain text in HTML email template
        
        Args:
            text (str): Plain text email
        
        Returns:
            str: HTML wrapped email
        """
        html_template = """<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    {text}
</body>
</html>"""
        
        return html_template.format(text=text)
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def generate_emails_batch(self, leads: list) -> list:
        """
        Generate emails for a batch of leads
        
        Args:
            leads (list): List of lead dictionaries
        
        Returns:
            list: Leads with generated_email added
        """
        self.logger.info(f"Generating emails for {len(leads)} leads...")
        
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        for i, lead in enumerate(leads, 1):
            result = self.generate_email(lead)
            results.append(result)
            
            # Count
            status = result.get('email_status', 'unknown')
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
            
            # Rate limiting
            time.sleep(0.2)
        
        self.logger.info(
            f"✅ Email generation complete! "
            f"Success: {successful}, Failed: {failed}, Skipped: {skipped}"
        )
        
        return results
    
    # ========================================================================
    # EMAIL PREVIEW
    # ========================================================================
    
    def get_email_preview(self, email_html: str, length: int = 200) -> str:
        """
        Get a text preview of generated email
        
        Args:
            email_html (str): HTML email content
            length (int): Preview length in characters
        
        Returns:
            str: Text preview
        """
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', email_html)
        return text[:length]
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def is_valid_email_html(self, email_html: str) -> bool:
        """
        Validate generated email HTML
        
        Args:
            email_html (str): Email HTML content
        
        Returns:
            bool: True if valid
        """
        if not email_html:
            return False
        
        # Must have minimum content
        if len(email_html) < 100:
            return False
        
        # Should contain HTML or basic text
        has_structure = any([
            '<' in email_html,   # Has HTML tags
            '\n' in email_html,  # Has line breaks
            len(email_html.split()) > 20  # Has enough words
        ])
        
        return has_structure


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test email generation
    """
    print("\n" + "="*60)
    print("TESTING EMAIL GENERATOR (GROQ ENGINE)")
    print("="*60 + "\n")
    
    generator = EmailGenerator()
    
    # Test 1: Generate single email
    print("Test 1: Generating personalized email...")
    
    test_lead = {
        'company_name': 'OpenAI',
        'business_summary': (
            'OpenAI is an AI research company that develops advanced language models '
            'and AI systems. They create tools like ChatGPT and GPT-4 that help '
            'businesses and developers build AI-powered applications.'
        ),
        'industry': 'AI & Technology',
    }
    
    result = generator.generate_email(test_lead)
    
    print(f"\n  Company: {result['company_name']}")
    print(f"  Status: {result['email_status']}")
    
    if result['generated_email']:
        preview = generator.get_email_preview(result['generated_email'], 300)
        print(f"\n  Email Preview:")
        print(f"  {preview}...")
    
    # Test 2: Batch processing
    print("\n" + "-"*60)
    print("\nTest 2: Batch email generation")
    
    test_leads = [
        {
            'company_name': 'OpenAI',
            'business_summary': (
                'OpenAI develops advanced AI language models and systems. '
                'They create ChatGPT and GPT-4 for business applications.'
            ),
            'industry': 'AI',
        },
        {
            'company_name': 'Company with no summary',
            'business_summary': '',
            'industry': 'Tech',
        },
    ]
    
    results = generator.generate_emails_batch(test_leads)
    print(f"\n✅ Generated emails for {len(results)} leads")
    
    # Count results
    successful = sum(1 for r in results if r.get('email_status') == 'success')
    print(f"   Successful: {successful}")
    
    # Show error report
    error_summary = error_tracker.get_error_summary()
    if error_summary:
        print(f"\n⚠️  Errors: {error_summary['total_errors']}")
    
    print("\n" + "="*60)
    print("✅ Email generator test completed!")
    print("="*60 + "\n")