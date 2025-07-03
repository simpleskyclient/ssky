import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

class ErrorResult:
    """Error result container that holds error information."""
    
    def __init__(self, message: str, http_code: int = 500, data: Any = None):
        self.message = message
        self.http_code = http_code
        self.data = data
        self.timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        self.is_error = True
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return create_error_response(
            message=self.message,
            http_code=self.http_code,
            data=self.data
        )
    
    def __str__(self) -> str:
        """String representation for stderr output."""
        return f"{self.http_code} {self.message}"

class DryRunResult:
    """Dry-run result container that holds preview information with JSON support."""
    
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
        self.timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        self.is_preview = True
    
    def to_json(self) -> str:
        """Convert to JSON string in ATProto PostView format (partial for dry-run)."""
        # Build facets structure
        facets = []
        
        # Add tag facets
        for tag in self.tags:
            if tag.get('name') and tag.get('byte_start') is not None and tag.get('byte_end') is not None:
                facets.append({
                    "features": [{"tag": tag['name'][1:], "$type": "app.bsky.richtext.facet#tag"}],
                    "index": {
                        "byteStart": tag['byte_start'],
                        "byteEnd": tag['byte_end'],
                        "$type": "app.bsky.richtext.facet#byteSlice"
                    },
                    "$type": "app.bsky.richtext.facet"
                })
        
        # Add link facets  
        for link in self.links:
            if link.get('uri') and link.get('byte_start') is not None and link.get('byte_end') is not None:
                facets.append({
                    "features": [{"uri": link['uri'], "$type": "app.bsky.richtext.facet#link"}],
                    "index": {
                        "byteStart": link['byte_start'],
                        "byteEnd": link['byte_end'],
                        "$type": "app.bsky.richtext.facet#byteSlice"
                    },
                    "$type": "app.bsky.richtext.facet"
                })
        
        # Add mention facets
        for mention in self.mentions:
            if mention.get('did') and mention.get('byte_start') is not None and mention.get('byte_end') is not None:
                facets.append({
                    "features": [{"did": mention['did'], "$type": "app.bsky.richtext.facet#mention"}],
                    "index": {
                        "byteStart": mention['byte_start'],
                        "byteEnd": mention['byte_end'],
                        "$type": "app.bsky.richtext.facet#byteSlice"
                    },
                    "$type": "app.bsky.richtext.facet"
                })
        
        # Build record structure
        record = {
            "$type": "app.bsky.feed.post",
            "text": self.message,
            "createdAt": self.timestamp
        }
        
        if facets:
            record["facets"] = facets
        
        # Build embed if card exists
        embed = None
        if self.card:
            embed = {
                "$type": "app.bsky.embed.external",
                "external": {
                    "$type": "app.bsky.embed.external#external",
                    "uri": self.card["uri"],
                    "title": self.card["title"],
                    "description": self.card["description"]
                }
            }
            if self.card.get("thumbnail"):
                embed["external"]["thumb"] = {"$type": "blob", "ref": {"$link": "preview-thumbnail"}}
        
        # Build reply reference if exists
        reply = None
        if self.reply_to:
            reply = {
                "parent": {"uri": self.reply_to, "cid": "preview-parent-cid"},
                "root": {"uri": self.reply_to, "cid": "preview-root-cid"},
                "$type": "app.bsky.feed.post#replyRef"
            }
        
        if reply:
            record["reply"] = reply
        
        # Build partial PostView structure (dry-run preview)
        post_view = {
            "$type": "app.bsky.feed.defs#postView",
            "record": record,
            "author": {
                "$type": "app.bsky.actor.defs#profileViewBasic",
                "did": "preview-author-did",
                "handle": "preview.bsky.social",
                "displayName": "Preview Author"
            }
        }
        
        if embed:
            post_view["embed"] = embed
        
        return json.dumps(post_view, ensure_ascii=False)
    
    def to_simple_json(self) -> str:
        """Convert to simplified JSON format for MCP."""
        data = {
            "preview": True,
            "message": self.message,
            "tags": [tag.get('name', '') for tag in self.tags],
            "links": [link.get('uri', '') for link in self.links],
            "mentions": [{"did": mention.get('did', ''), "handle": mention.get('handle', '')} for mention in self.mentions],
            "images": list(self.images),
            "card": self.card,
            "reply_to": self.reply_to,
            "quote": self.quote
        }
        return create_success_response(data=data, message="Dry run preview")
    
    def to_list(self) -> list:
        """Convert to list format for backward compatibility."""
        result = []
        result.append([self.message])
        for tag in self.tags:
            result.append(['Tag', tag.get('name', '')])
        for link in self.links:
            result.append(['Link', link.get('uri', '')])
        for mention in self.mentions:
            result.append(['Mention', mention.get('did', ''), mention.get('handle', '')])
        for img in self.images:
            result.append(['Image', img])
        if self.card is not None:
            result.append(['Card', self.card["uri"], self.card['title'], self.card['description'], self.card['thumbnail']])
        if self.reply_to:
            result.append(['Reply to', self.reply_to])
        if self.quote:
            result.append(['Quote', self.quote])
        return result
    
    def print(self, format: str, output: str = None, delimiter: str = ' ') -> None:
        """Print method compatible with PostDataList/ProfileList interface."""
        if output:
            # File output - use text format
            filename = f"dry-run-{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            import os
            path = os.path.join(output, filename)
            with open(path, 'w') as f:
                for item in self.to_list():
                    f.write(delimiter.join(filter(lambda s: s is not None, item)))
                    f.write('\n')
        else:
            # Console output
            if format == 'json':
                print(self.to_json())
            elif format == 'simple_json':
                print(self.to_simple_json())
            else:
                # Text format - print each item
                for item in self.to_list():
                    print(delimiter.join(filter(lambda s: s is not None, item)))

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

def create_success_response(data: Any = None, message: str = "Success", http_code: int = 200) -> str:
    """Create a success JSON response.
    
    Args:
        data: Response data
        message: Success message
        http_code: HTTP status code (default: 200)
    
    Returns:
        JSON string with success format
    """
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