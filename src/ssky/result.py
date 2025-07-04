"""
Result classes, error handling, and exception definitions for ssky.

This module contains all result types, error handling utilities, and custom exceptions
used throughout the ssky application.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional
import sys


class ErrorResult:
    """Represents an error result with message and HTTP status code."""
    
    def __init__(self, message: str, http_code: int = 500, data: Any = None):
        self.message = message
        self.http_code = http_code
        self.data = data

    def to_json(self) -> str:
        """Convert to JSON format."""
        from .util import create_error_response
        return create_error_response(
            message=self.message,
            http_code=self.http_code,
            data=self.data
        )

    def __str__(self) -> str:
        return self.message


class SuccessResult:
    """Represents a successful result with optional data and warnings."""
    
    def __init__(self, data: Any = None, message: str = "Success", warnings: list = None):
        self.data = data
        self.message = message
        self.warnings = warnings or []

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(warning)

    def to_json(self) -> str:
        """Convert to JSON format."""
        from .util import create_success_response
        
        # If data has its own to_json method, use it directly
        if hasattr(self.data, 'to_json'):
            return self.data.to_json()
        else:
            return create_success_response(
                data=self.data,
                message=self.message,
                warnings=self.warnings if self.warnings else None
            )

    def print(self, format: str, output: str = None, delimiter: str = ' ') -> None:
        """Print the success result in the specified format."""
        if format in ('json', 'simple_json'):
            content = self.to_json()
        else:
            content = str(self)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(content + '\n')
        else:
            print(content)
            # Print warnings to stderr in text format
            if self.warnings and format not in ('json', 'simple_json'):
                for warning in self.warnings:
                    print(f"Warning: {warning}", file=sys.stderr)

    def __str__(self) -> str:
        return self.message


class DryRunResult:
    """Represents a dry run result with detailed information about what would be posted."""
    
    def __init__(self, message: str, tags: list = None, links: list = None, 
                 mentions: list = None, images: list = None, card: dict = None, 
                 reply_to: str = None, quote: str = None):
        self.message = message
        self.tags = tags or []
        self.links = links or []
        self.mentions = mentions or []
        self.images = images or []
        self.card = card
        self.reply_to = reply_to
        self.quote = quote

    def to_json(self) -> str:
        """Convert to JSON format."""
        data = {
            "message": self.message,
            "tags": self.tags,
            "links": self.links,
            "mentions": self.mentions,
            "images": [
                {
                    "path": img.get("path", ""),
                    "alt_text": img.get("alt_text", ""),
                    "size": img.get("size", 0),
                    "mime_type": img.get("mime_type", "")
                } for img in self.images
            ],
            "card": self.card,
            "reply_to": self.reply_to,
            "quote": self.quote
        }
        
        response = {
            "status": "ok",
            "http_code": 200,
            "message": "Dry run completed",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "data": data
        }
        
        return json.dumps(response, ensure_ascii=False, separators=(',', ':'))

    def to_simple_json(self) -> str:
        """Convert to simplified JSON format."""
        data = {
            "message": self.message,
            "tags": len(self.tags),
            "links": len(self.links), 
            "mentions": len(self.mentions),
            "images": len(self.images),
            "has_card": self.card is not None,
            "has_reply_to": self.reply_to is not None,
            "has_quote": self.quote is not None
        }
        
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))

    def to_list(self) -> list:
        """Convert to list format for consistent output."""
        items = []
        
        # Main message
        items.append(f"Message: {self.message}")
        
        # Tags
        if self.tags:
            items.append(f"Tags: {', '.join(self.tags)}")
        
        # Links
        if self.links:
            items.append(f"Links: {', '.join(self.links)}")
        
        # Mentions
        if self.mentions:
            items.append(f"Mentions: {', '.join(self.mentions)}")
        
        # Images
        if self.images:
            image_info = []
            for img in self.images:
                info = img.get("path", "unknown")
                if img.get("alt_text"):
                    info += f" (alt: {img['alt_text']})"
                image_info.append(info)
            items.append(f"Images: {', '.join(image_info)}")
        
        # Card
        if self.card:
            items.append(f"Card: {self.card.get('title', 'Unknown')}")
        
        # Reply and Quote
        if self.reply_to:
            items.append(f"Reply to: {self.reply_to}")
        if self.quote:
            items.append(f"Quote: {self.quote}")
        
        return items

    def print(self, format: str, output: str = None, delimiter: str = ' ') -> None:
        """Print the dry run result in the specified format."""
        from .util import should_use_json_format
        
        if should_use_json_format(format=format):
            if format == 'simple_json':
                content = self.to_simple_json()
            else:
                content = self.to_json()
        else:
            # Default text format
            items = self.to_list()
            content = delimiter.join(items) if delimiter != ' ' else '\n'.join(items)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(content + '\n')
        else:
            print(content)

    def __str__(self) -> str:
        return f"Dry run: {self.message}"


# Custom Exception Classes
class SskyError(Exception):
    """Base exception for ssky application errors."""
    
    def __init__(self, message: str, http_code: int = 500, original_exception: Exception = None):
        super().__init__(message)
        self.message = message
        self.http_code = http_code
        self.original_exception = original_exception


class AtProtocolSskyError(SskyError):
    """Wrapper for AtProtocolError exceptions."""
    
    def __init__(self, original_error):
        # Use existing handle_atprotocol_error() logic
        error_result = handle_atprotocol_error(original_error)
        super().__init__(
            message=error_result.message,
            http_code=error_result.http_code,
            original_exception=original_error
        )


# Specific Error Classes
class SessionError(SskyError):
    """Session-related errors."""
    def __init__(self):
        super().__init__("No valid session available", 401)


class InvalidActorError(SskyError):
    """Invalid actor identifier errors."""
    def __init__(self):
        super().__init__("Invalid actor identifier", 400)


class NotFoundError(SskyError):
    """Resource not found errors."""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", 404)


class OperationFailedError(SskyError):
    """Operation failed errors."""
    def __init__(self, operation: str):
        super().__init__(f"Failed to {operation}", 500)


# Login-specific errors
class EmptyCredentialsError(SskyError):
    """Empty credentials provided errors."""
    def __init__(self):
        super().__init__("Empty credentials provided", 400)


class InvalidCredentialFormatError(SskyError):
    """Invalid credential format errors."""
    def __init__(self):
        super().__init__("Invalid credential format - expected 'handle:password'", 400)


class ProfileUnavailableError(SskyError):
    """Profile not available errors."""
    def __init__(self):
        super().__init__("Profile not available", 401)


class ProfileUnavailableAfterLoginError(SskyError):
    """Profile not available after login errors."""
    def __init__(self):
        super().__init__("Profile not available after login", 500)


class LoginUnexpectedError(SskyError):
    """Unexpected login errors."""
    def __init__(self, exception: Exception):
        super().__init__(f"Unexpected error during login: {str(exception)}", 500, exception)


# Validation errors
class TooManyImagesError(SskyError):
    """Too many image files errors."""
    def __init__(self):
        super().__init__("Too many image files", 400)


# Relationship errors
class NotFollowingError(SskyError):
    """Not following user errors."""
    def __init__(self, actor: str):
        super().__init__(f"You are not following {actor}", 404)


class InvalidUriError(SskyError):
    """Invalid URI errors."""
    def __init__(self, uri: str = None):
        message = f"Invalid URI: {uri}" if uri else "URI cannot be empty"
        super().__init__(message, 400)


# Error handling functions
def get_http_status_from_exception(e) -> int:
    """Extract HTTP status code from exception.
    
    Args:
        e: Exception object
    
    Returns:
        HTTP status code
    """
    if hasattr(e, 'response') and e.response is not None:
        if hasattr(e.response, 'status_code'):
            return e.response.status_code
    
    # Default mappings for common exceptions
    if 'timeout' in str(e).lower():
        return 408  # Request Timeout
    elif 'connection' in str(e).lower():
        return 503  # Service Unavailable
    elif 'authentication' in str(e).lower() or 'login' in str(e).lower():
        return 401  # Unauthorized
    elif 'permission' in str(e).lower() or 'forbidden' in str(e).lower():
        return 403  # Forbidden
    elif 'not found' in str(e).lower():
        return 404  # Not Found
    else:
        return 500  # Internal Server Error


def handle_atprotocol_error(e) -> ErrorResult:
    """Handle AtProtocolError and its subclasses and return standardized ErrorResult.
    
    Args:
        e: AtProtocolError or its subclass exception
    
    Returns:
        ErrorResult with extracted message and HTTP code
    """
    # Check for specific exception types first
    import atproto_client.exceptions
    if isinstance(e, atproto_client.exceptions.LoginRequiredError):
        http_code = 401  # Unauthorized - always use 401 for login required
    else:
        http_code = get_http_status_from_exception(e)
    
    # Extract error message with improved logic
    if (hasattr(e, 'response') and e.response is not None and 
        hasattr(e.response, 'content') and hasattr(e.response.content, 'message')):
        message = e.response.content.message
    elif str(e) and len(str(e)) > 0:
        message = str(e)
    else:
        message = e.__class__.__name__
    
    return ErrorResult(message, http_code)


# Internal helper function
def _create_error(message: str, http_code: int = 500) -> ErrorResult:
    """Create a standardized ErrorResult. (Internal use only)
    
    Args:
        message: Error message
        http_code: HTTP status code
    
    Returns:
        ErrorResult instance
    """
    return ErrorResult(message, http_code)


# Legacy helper functions for backward compatibility (deprecated)
def create_session_error() -> ErrorResult:
    """Create a 'No valid session available' error. (Deprecated: Use SessionError exception)"""
    return _create_error("No valid session available", 401)


def create_invalid_actor_error() -> ErrorResult:
    """Create an 'Invalid actor identifier' error. (Deprecated: Use InvalidActorError exception)"""
    return _create_error("Invalid actor identifier", 400)


def create_not_found_error(resource: str = "Resource") -> ErrorResult:
    """Create a resource not found error. (Deprecated: Use NotFoundError exception)"""
    return _create_error(f"{resource} not found", 404)


def create_operation_failed_error(operation: str) -> ErrorResult:
    """Create an operation failed error. (Deprecated: Use OperationFailedError exception)"""
    return _create_error(f"Failed to {operation}", 500)


def create_empty_credentials_error() -> ErrorResult:
    """Create an 'Empty credentials provided' error. (Deprecated: Use EmptyCredentialsError exception)"""
    return _create_error("Empty credentials provided", 400)


def create_invalid_credential_format_error() -> ErrorResult:
    """Create an 'Invalid credential format' error. (Deprecated: Use InvalidCredentialFormatError exception)"""
    return _create_error("Invalid credential format - expected 'handle:password'", 400)


def create_profile_unavailable_error() -> ErrorResult:
    """Create a 'Profile not available' error. (Deprecated: Use ProfileUnavailableError exception)"""
    return _create_error("Profile not available", 401)


def create_profile_unavailable_after_login_error() -> ErrorResult:
    """Create a 'Profile not available after login' error. (Deprecated: Use ProfileUnavailableAfterLoginError exception)"""
    return _create_error("Profile not available after login", 500)


def create_login_unexpected_error(exception: Exception) -> ErrorResult:
    """Create an unexpected login error. (Deprecated: Use LoginUnexpectedError exception)"""
    return _create_error(f"Unexpected error during login: {str(exception)}", 500)


def create_too_many_images_error() -> ErrorResult:
    """Create a 'Too many image files' error. (Deprecated: Use TooManyImagesError exception)"""
    return _create_error("Too many image files", 400)


def create_not_following_error(actor: str) -> ErrorResult:
    """Create a 'You are not following' error. (Deprecated: Use NotFollowingError exception)"""
    return _create_error(f"You are not following {actor}", 404) 