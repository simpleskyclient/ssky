import json
import re
from datetime import datetime, timezone
from typing import Any, Optional
 
def summarize(source, length_max=0):
    if source is None:
        return ''
    else:
        summary = re.sub(r'\s', '_', ''.join(list(map(lambda c: c if c > ' ' else ' ', source.rstrip()))))
        if length_max > 0 and len(summary) > length_max:
            summary = ''.join(summary[:length_max - 2]) + '..'
        return summary

def join_uri_cid(uri, cid) -> str:
    return '::'.join([uri, cid])

def disjoin_uri_cid(uri_cid) -> tuple:
    pair = uri_cid.split('::', 1)
    return pair[0], pair[1]

def is_joined_uri_cid(uri_cid) -> bool:
    return '::' in uri_cid

def create_json_response(
    status: str,
    http_code: int,
    message: str,
    data: Any = None,
    timestamp: Optional[str] = None
) -> str:
    """Create a consistent JSON response format.
    
    Args:
        status: Status string ("ok" or "error")
        http_code: HTTP status code
        message: Human-readable message
        data: Response data (can be None)
        timestamp: ISO timestamp (auto-generated if None)
    
    Returns:
        JSON string with consistent format
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    response = {
        "status": status,
        "http_code": http_code,
        "message": message,
        "timestamp": timestamp,
        "data": data
    }
    
    return json.dumps(response, ensure_ascii=False, separators=(',', ':'))

def create_success_response(data: Any = None, message: str = "Success", http_code: int = 200, warnings: Optional[list] = None) -> str:
    """Create a success JSON response.
    
    Args:
        data: Response data
        message: Success message
        http_code: HTTP status code (default: 200)
        warnings: List of warning messages to include in the response
    
    Returns:
        JSON string with success format
    """
    # Add warnings to message if present
    if warnings:
        warning_text = "; ".join(warnings)
        message = f"{message} (Warnings: {warning_text})"
    
    return create_json_response(
        status="ok",
        http_code=http_code,
        message=message,
        data=data
    )

def create_error_response(
    message: str,
    http_code: int = 500,
    data: Any = None
) -> str:
    """Create an error JSON response.
    
    Args:
        message: Error message
        http_code: HTTP status code
        data: Additional error data
    
    Returns:
        JSON string with error format
    """
    return create_json_response(
        status="error",
        http_code=http_code,
        message=message,
        data=data
    )

def should_use_json_format(**kwargs) -> bool:
    """Check if JSON format should be used based on kwargs.
    
    Args:
        **kwargs: Arguments that may contain 'format' key
    
    Returns:
        True if JSON format should be used
    """
    format_type = kwargs.get('format', '')
    return format_type in ('json', 'simple_json')