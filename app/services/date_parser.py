"""
Date parsing service for extracting dates from natural language text.
"""
from datetime import datetime
import dateparser
from typing import Optional

def parse_date(text: str) -> Optional[datetime]:
    """
    Parse a date from natural language text.
    
    Args:
        text: The text containing the date (e.g., "yesterday", "last friday", "on Jan 15")
        
    Returns:
        datetime object if found, None otherwise
    """
    # Settings for dateparser
    settings = {
        'PREFER_DATES_FROM': 'past',  # Assume past dates for ambiguous inputs like "Monday"
        'RELATIVE_BASE': datetime.now(),
        'RETURN_AS_TIMEZONE_AWARE': False
    }
    
    # Try parsing
    dt = dateparser.parse(text, settings=settings)
    
    if dt:
        # If the date is in the future (and wasn't explicitly future), it might be a mistake
        # depending on context, but for finance tracking usually it's past.
        # However, dateparser with PREFER_DATES_FROM='past' handles "Monday" correctly 
        # as last Monday.
        return dt
        
    return None
