"""
AI Lead Generation Project
==========================

A Python-based automation system for finding company leads, extracting business info,
and generating personalized outreach emails using AI.

Author: Your Name
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Import commonly used classes and functions
from .error_handler import (
    LoggerSetup,
    ErrorTracker,
    LeadGenerationException,
    ConfigurationError,
    APIError,
    WebScrapingError,
)
from .lead_discovery import LeadDiscovery
from .main import LeadGenerationPipeline

__all__ = [
    "LoggerSetup",
    "ErrorTracker",
    "LeadGenerationException",
    "ConfigurationError",
    "APIError",
    "WebScrapingError",
    "LeadDiscovery",
    "LeadGenerationPipeline",
]