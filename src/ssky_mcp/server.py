#!/usr/bin/env python3
"""
Official MCP SDK implementation for ssky (Simple Bluesky Client)
"""

import json
import logging
import subprocess
import sys
from importlib.metadata import version, PackageNotFoundError
from fastmcp import FastMCP

# Import ssky utilities (now we can import directly!)
from ssky.util import create_success_response, create_error_response

# Set logging level to WARNING and above for stderr output
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

# Set the root logger to WARNING level
logging.getLogger().setLevel(logging.WARNING)

# Suppress FastMCP INFO logs specifically
logging.getLogger("FastMCP").setLevel(logging.WARNING)
logging.getLogger("fastmcp").setLevel(logging.WARNING)
logging.getLogger("FastMCP.fastmcp.server.server").setLevel(logging.WARNING)

# Create logger for this module
logger = logging.getLogger("ssky_mcp_server")

# Create FastMCP server
mcp = FastMCP("ssky")

# Set the MCP server version (same as ssky package)
def get_mcp_server_version():
    """Get the MCP server version (uses ssky package version)"""
    try:
        return version("ssky")
    except PackageNotFoundError:
        logger.warning("Could not find ssky package version, using fallback")
        return "unknown"

mcp._mcp_server.version = get_mcp_server_version()

def format_success_response(data: str) -> str:
    """Format success response for MCP (expects JSON data)"""
    
    if data:
        # Data should already be JSON from --simple-json, return as-is
        try:
            parsed_data = json.loads(data)
            # If it's already in the new format (has status field), return as-is
            if isinstance(parsed_data, dict) and 'status' in parsed_data:
                return data
            # Otherwise, wrap it in the new format
            return create_success_response(data=parsed_data)
        except json.JSONDecodeError as e:
            # If not JSON, wrap it as string data
            logger.warning(f"format_success_response received non-JSON data, wrapping it: {str(e)[:100]}...")
            return create_success_response(data=data)
    else:
        # Empty response case
        return create_success_response(data=None)

@mcp.tool()
def ssky_get(
    param: str = "", 
    limit: int = 25, 
    delimiter: str = "",
    output_dir: str = ""
) -> str:
    """Get posts from Bluesky timeline or specific user
    
    Args:
        param: URI(at://...), DID(did:...), handle, "myself", or none for timeline
        limit: Number of posts to retrieve (default: 25, same as ssky command)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "get"]
    
    # Add limit option
    args.extend(["-N", str(limit)])
    
    # Always use simple-json for MCP
    args.append("-S")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["-D", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["-O", output_dir])
    
    # Add positional parameter (URI, DID, handle)
    if param:
        args.append(param)
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_get failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_get command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_get unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()  
def ssky_post(
    message: str = "", 
    dry_run: bool = False, 
    images: str = "", 
    quote_uri: str = "", 
    reply_to_uri: str = "", 
    delimiter: str = "", 
    output_dir: str = ""
) -> str:
    """Post message to Bluesky
    
    Args:
        message: The message to post
        dry_run: If True, show what would be posted without actually posting
        images: Comma-separated list of image file paths to attach
        quote_uri: URI of post to quote (at://...)
        reply_to_uri: URI of post to reply to (at://...)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "post"]
    
    # Add dry run option
    if dry_run:
        args.append("--dry")
    
    # Add image files if specified
    if images:
        image_paths = [path.strip() for path in images.split(",") if path.strip()]
        for image_path in image_paths:
            args.extend(["--image", image_path])
    
    # Add quote option if specified
    if quote_uri:
        args.extend(["--quote", quote_uri])
    
    # Add reply-to option if specified
    if reply_to_uri:
        args.extend(["--reply-to", reply_to_uri])
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    # Add message as last argument (if provided)
    if message:
        args.append(message)
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_post failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_post command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_post unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_search(
    query: str, 
    limit: int = 25, 
    author: str = "", 
    since: str = "", 
    until: str = "", 
    delimiter: str = "", 
    output_dir: str = ""
) -> str:
    """Search posts on Bluesky
    
    Args:
        query: Search query
        limit: Number of results to return (default: 25, same as ssky command)
        author: Author handle, DID, or "myself" to filter by
        since: Since timestamp (ex. 2001-01-01T00:00:00Z, "today", "yesterday")
        until: Until timestamp (ex. 2099-12-31T23:59:59Z, "today", "yesterday")
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "search", query, "--limit", str(limit)]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add author filter if specified
    if author:
        args.extend(["--author", author])
    
    # Add since filter if specified
    if since:
        args.extend(["--since", since])
    
    # Add until filter if specified
    if until:
        args.extend(["--until", until])
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_search failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_search command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_search unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_profile(handle: str, delimiter: str = "", output_dir: str = "") -> str:
    """Show user profile information
    
    Args:
        handle: User handle, DID, or "myself" (e.g., user.bsky.social)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "profile", handle]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_profile failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_profile command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_profile unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_user(query: str, limit: int = 25, delimiter: str = "", output_dir: str = "") -> str:
    """Search users on Bluesky
    
    Args:
        query: Search query for users
        limit: Number of results to return (default: 25, same as ssky command)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "user", query, "--limit", str(limit)]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_user failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_user command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_user unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_follow(handle: str, delimiter: str = "", output_dir: str = "") -> str:
    """Follow a user on Bluesky
    
    Args:
        handle: User handle, DID, or "myself" to follow
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "follow", handle]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_follow failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_follow command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_follow unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_unfollow(handle: str, delimiter: str = "", output_dir: str = "") -> str:
    """Unfollow a user on Bluesky
    
    Args:
        handle: User handle, DID, or "myself" to unfollow
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "unfollow", handle]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_unfollow failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_unfollow command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_unfollow unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_repost(post_uri: str, delimiter: str = "", output_dir: str = "") -> str:
    """Repost a post on Bluesky
    
    Args:
        post_uri: URI of the post to repost (at://...)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "repost", post_uri]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_repost failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_repost command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_repost unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_unrepost(post_uri: str, delimiter: str = "", output_dir: str = "") -> str:
    """Unrepost (remove repost) a post on Bluesky
    
    Args:
        post_uri: URI of the post to unrepost (at://...)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "unrepost", post_uri]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    # Add delimiter if specified
    if delimiter:
        args.extend(["--delimiter", delimiter])
    
    # Add output directory if specified
    if output_dir:
        args.extend(["--output", output_dir])
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return format_success_response(result.stdout.strip())
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_unrepost failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_unrepost command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_unrepost unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

@mcp.tool()
def ssky_delete(post_uri: str) -> str:
    """Delete a post on Bluesky
    
    Args:
        post_uri: URI of the post to delete (at://...)
    """
    args = ["ssky", "delete", post_uri]
    
    # Always use simple-json for MCP
    args.append("--simple-json")
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout.strip() if result.stdout.strip() else "Post deleted successfully"
            return format_success_response(output)
        else:
            error_msg = result.stderr.strip()
            logger.error(f"ssky_delete failed with return code {result.returncode}: {error_msg}")
            # Try to parse error as JSON first
            try:
                error_json = json.loads(error_msg)
                if isinstance(error_json, dict) and 'status' in error_json:
                    # Already in new format
                    return error_msg
            except json.JSONDecodeError:
                pass
            return create_error_response(message=error_msg, http_code=result.returncode if result.returncode != 0 else 500)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_delete command timed out: {' '.join(args)}")
        return create_error_response(message="Command timed out", http_code=408)
    except Exception as e:
        logger.error(f"ssky_delete unexpected error: {str(e)}")
        return create_error_response(message=str(e), http_code=500)

def main():
    """Main entry point for the MCP server."""
    import sys
    
    # Handle version request
    if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v']:
        print(f"ssky MCP server version {get_mcp_server_version()}")
        return
    
    logger.info(f"Starting ssky MCP server version {get_mcp_server_version()}")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
        pass

if __name__ == "__main__":
    main() 