"""Input validation utilities for the diabetes monitoring bot.

Provides validation functions for user input and data integrity.
"""
import re
from typing import Optional
from datetime import datetime


def validate_telegram_id(telegram_id: str) -> bool:
    """
    Validate that a telegram ID is in the correct format.
    
    Args:
        telegram_id: The telegram ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not telegram_id:
        return False
    
    # Telegram IDs should be numeric strings
    return telegram_id.isdigit()


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Validate that a date range is valid.
    
    Args:
        start_date: The start date
        end_date: The end date
        
    Returns:
        bool: True if valid (start <= end), False otherwise
    """
    return start_date <= end_date


def validate_severity_rating(rating: str) -> bool:
    """
    Validate that a severity rating is valid (1-5).
    
    Args:
        rating: The rating to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        rating_int = int(rating)
        return 1 <= rating_int <= 5
    except (ValueError, TypeError):
        return False


def sanitize_user_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: The text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Remove any potential HTML/Markdown tags
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*{2,}', '*', text)  # Limit multiple asterisks
    text = re.sub(r'_{2,}', '_', text)   # Limit multiple underscores
    
    # Limit length to prevent spam
    max_length = 1000
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()


def validate_export_days(days: Optional[int]) -> int:
    """
    Validate and return export days within acceptable range.
    
    Args:
        days: Number of days to export (None for default)
        
    Returns:
        int: Valid number of days
    """
    from bot_config.bot_constants import ExportSettings
    
    if days is None:
        return ExportSettings.DEFAULT_EXPORT_DAYS
    
    # Ensure days is within reasonable bounds
    min_days = 1
    max_days = 365
    
    return max(min_days, min(days, max_days))