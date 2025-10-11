"""Utility functions for the Website Chatbot."""

import re
from urllib.parse import urlparse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate if a URL is properly formatted and safe to scrape.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"
    
    # Basic format validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, "Invalid URL format. Must start with http:// or https://"
    
    try:
        parsed = urlparse(url)
        
        # Check for valid scheme
        if parsed.scheme not in ['http', 'https']:
            return False, "URL must use http or https protocol"
        
        # Check for valid netloc
        if not parsed.netloc:
            return False, "Invalid URL: missing domain"
        
        # Block potentially dangerous URLs
        dangerous_patterns = [
            r'file://',
            r'ftp://',
            r'javascript:',
            r'data:',
            r'about:',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False, f"URL scheme not allowed for security reasons"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False, "Invalid URL format"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: The string to sanitize
        max_length: Maximum length of the filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Truncate if too long
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"
    
    return filename


def format_sources(sources: list[str], max_sources: int = 5) -> str:
    """
    Format a list of source URLs for display.
    
    Args:
        sources: List of source URLs
        max_sources: Maximum number of sources to display
        
    Returns:
        Formatted string of sources
    """
    if not sources:
        return "No sources available"
    
    unique_sources = list(dict.fromkeys(sources))[:max_sources]
    
    if len(sources) > max_sources:
        return "\n".join(unique_sources) + f"\n... and {len(sources) - max_sources} more"
    
    return "\n".join(unique_sources)


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

