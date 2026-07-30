"""
error_handler.py - Logging & Error Handling
=============================================
Centralized logging configuration and error handling utilities.
All modules use this for consistent logging.
"""

import logging
import logging.handlers
from pathlib import Path
from .config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT, DEBUG_MODE


class LoggerSetup:
    """
    Setup centralized logging for the entire project
    """
    
    _logger = None
    
    @classmethod
    def get_logger(cls, name):
        """
        Get or create a logger instance
        
        Args:
            name (str): Logger name (usually __name__)
        
        Returns:
            logging.Logger: Configured logger instance
        """
        if cls._logger is None:
            cls._setup_logging()
        
        return logging.getLogger(name)
    
    @classmethod
    def _setup_logging(cls):
        """
        Configure logging for the project:
        - Console output (INFO level)
        - File output (DEBUG level)
        - Rotating file handler (max 5MB per file, keep 5 files)
        """
        
        # Ensure logs directory exists
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture everything
        
        # Create formatters
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        
        # 1. Console Handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 2. File Handler (DEBUG and above, with rotation)
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_FILE,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=5,  # Keep 5 backup files
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"⚠️  Could not setup file logging: {e}")
        
        # Prevent duplicate logs
        root_logger.propagate = False
        
        cls._logger = root_logger


# Initialize logging on import
LoggerSetup._setup_logging()


# ============================================================================
# EXCEPTION CLASSES
# ============================================================================

class LeadGenerationException(Exception):
    """Base exception for all lead generation errors"""
    pass


class ConfigurationError(LeadGenerationException):
    """Raised when configuration is invalid"""
    pass


class APIError(LeadGenerationException):
    """Raised when API calls fail"""
    pass


class WebScrapingError(LeadGenerationException):
    """Raised when website scraping fails"""
    pass


class DataValidationError(LeadGenerationException):
    """Raised when data validation fails"""
    pass


class GoogleSheetsError(LeadGenerationException):
    """Raised when Google Sheets operations fail"""
    pass


class EmailGenerationError(LeadGenerationException):
    """Raised when email generation fails"""
    pass


class DomainExtractionError(LeadGenerationException):
    """Raised when domain extraction fails"""
    pass


# ============================================================================
# ERROR TRACKING
# ============================================================================

class ErrorTracker:
    """
    Track errors and build comprehensive error report
    """
    
    def __init__(self):
        """Initialize error tracker"""
        self.errors = []
        self.logger = LoggerSetup.get_logger(__name__)
    
    def add_error(self, lead_name, error_type, error_message, step):
        """
        Add an error to the tracker
        
        Args:
            lead_name (str): Company/lead name
            error_type (str): Type of error (e.g., "WebScrapingError")
            error_message (str): Error message/details
            step (str): Which step failed (e.g., "website_scraping")
        """
        error_record = {
            "lead_name": lead_name,
            "error_type": error_type,
            "message": error_message,
            "step": step,
        }
        self.errors.append(error_record)
        
        # Log immediately
        self.logger.warning(
            f"Error for '{lead_name}' at step '{step}': "
            f"{error_type} - {error_message}"
        )
    
    def get_error_summary(self):
        """Get summary of all errors"""
        if not self.errors:
            return None
        
        summary = {
            "total_errors": len(self.errors),
            "errors_by_type": {},
            "errors_by_step": {},
            "errors": self.errors,
        }
        
        # Count by type
        for error in self.errors:
            error_type = error["error_type"]
            summary["errors_by_type"][error_type] = \
                summary["errors_by_type"].get(error_type, 0) + 1
            
            step = error["step"]
            summary["errors_by_step"][step] = \
                summary["errors_by_step"].get(step, 0) + 1
        
        return summary
    
    def print_error_report(self):
        """Print formatted error report"""
        summary = self.get_error_summary()
        
        if not summary:
            self.logger.info("✅ No errors encountered!")
            return
        
        print("\n" + "="*70)
        print("ERROR REPORT")
        print("="*70)
        
        print(f"\n📊 TOTAL ERRORS: {summary['total_errors']}")
        
        print("\n📈 Errors by Type:")
        for error_type, count in summary["errors_by_type"].items():
            print(f"  - {error_type}: {count}")
        
        print("\n📍 Errors by Step:")
        for step, count in summary["errors_by_step"].items():
            print(f"  - {step}: {count}")
        
        print("\n📋 Detailed Error List:")
        for i, error in enumerate(summary["errors"], 1):
            print(f"\n  {i}. {error['lead_name']}")
            print(f"     Step: {error['step']}")
            print(f"     Type: {error['error_type']}")
            print(f"     Message: {error['message']}")
        
        print("\n" + "="*70 + "\n")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_section(title: str, level: str = "INFO"):
    """Log a section header with clean formatting."""
    logger = LoggerSetup.get_logger(__name__)
    separator = "=" * 60
    logger.log(
        getattr(logging, level.upper()),
        f"\n{separator}\n  {title}\n{separator}"
    )


def log_progress(current, total, item_name=""):
    """
    Log progress of batch processing
    
    Args:
        current (int): Current item number
        total (int): Total items
        item_name (str): Name of current item
    """
    logger = LoggerSetup.get_logger(__name__)
    percentage = (current / total) * 100
    
    status = f"Progress: {current}/{total} ({percentage:.1f}%)"
    if item_name:
        status += f" - {item_name}"
    
    logger.info(status)


def handle_exception(exception, context=""):
    """
    Handle exceptions with logging
    
    Args:
        exception (Exception): The exception
        context (str): Additional context information
    """
    logger = LoggerSetup.get_logger(__name__)
    
    error_msg = f"{type(exception).__name__}: {str(exception)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    
    logger.exception(error_msg)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Test logging setup
    """
    
    print("\n" + "="*60)
    print("TESTING ERROR HANDLER")
    print("="*60 + "\n")
    
    # Get logger
    logger = LoggerSetup.get_logger(__name__)
    
    # Test different log levels
    logger.debug("This is a DEBUG message (visible in file only)")
    logger.info("This is an INFO message (visible in console & file)")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Test error tracker
    print("\n" + "="*60)
    print("TESTING ERROR TRACKER")
    print("="*60 + "\n")
    
    tracker = ErrorTracker()
    
    # Simulate some errors
    tracker.add_error(
        "TechStartup Inc",
        "WebScrapingError",
        "Connection timeout after 10 seconds",
        "website_scraping"
    )
    
    tracker.add_error(
        "DataCorp Solutions",
        "APIError",
        "OpenRouter API returned 429 (rate limit exceeded)",
        "ai_summarization"
    )
    
    tracker.add_error(
        "TechStartup Inc",
        "EmailGenerationError",
        "Invalid template variables",
        "email_generation"
    )
    
    # Print report
    tracker.print_error_report()
    
    print("✅ Error handler test completed!")
    print(f"📁 Log file: {LOG_FILE}")
    print("\n" + "="*60 + "\n")