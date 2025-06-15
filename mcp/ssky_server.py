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

# Set the correct version from installed package metadata
def get_version():
    try:
        return version("ssky")
    except PackageNotFoundError:
        logger.warning("Could not find ssky package version, using fallback")
        return "unknown"  # fallback version

mcp._mcp_server.version = get_version()

def format_success_response(data: str) -> str:
    """Format success response for MCP (expects JSON data)"""
    if data:
        # Data should already be JSON from --simple-json, return as-is
        try:
            json.loads(data)  # Validate it's valid JSON
            return data
        except json.JSONDecodeError as e:
            # If not JSON, wrap it (fallback case)
            logger.warning(f"format_success_response received non-JSON data, wrapping it: {str(e)[:100]}...")
            try:
                return json.dumps({
                    "error": False,
                    "message": "Success",
                    "timestamp": None,
                    "data": data
                }, ensure_ascii=False)
            except Exception as json_error:
                logger.error(f"format_success_response failed to create JSON wrapper: {str(json_error)}")
                # Last resort: return a simple JSON string
                return '{"error": false, "message": "Success", "data": "Response formatting error"}'
    else:
        # Empty response case
        try:
            return json.dumps({
                "error": False,
                "message": "Success",
                "timestamp": None,
                "data": None
            }, ensure_ascii=False)
        except Exception as json_error:
            logger.error(f"format_success_response failed to create empty JSON response: {str(json_error)}")
            # Last resort: return a simple JSON string
            return '{"error": false, "message": "Success", "data": null}'

@mcp.tool()
def ssky_get(
    param: str = "", 
    limit: int = 25, 
    delimiter: str = "",
    output_dir: str = ""
) -> str:
    """Get posts from Bluesky timeline or specific user
    
    Args:
        param: URI(at://...), DID(did:...), handle, or none for timeline
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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_get command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_get unexpected error: {str(e)}")
        raise RuntimeError(str(e))

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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_post command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_post unexpected error: {str(e)}")
        raise RuntimeError(str(e))

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
        author: Author handle or DID to filter by
        since: Since timestamp (ex. 2001-01-01T00:00:00Z)
        until: Until timestamp (ex. 2099-12-31T23:59:59Z)
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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_search command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_search unexpected error: {str(e)}")
        raise RuntimeError(str(e))

@mcp.tool()
def ssky_profile(handle: str, delimiter: str = "", output_dir: str = "") -> str:
    """Show user profile information
    
    Args:
        handle: User handle (e.g., user.bsky.social)
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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_profile command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_profile unexpected error: {str(e)}")
        raise RuntimeError(str(e))

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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_user command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_user unexpected error: {str(e)}")
        raise RuntimeError(str(e))

@mcp.tool()
def ssky_follow(handle: str, delimiter: str = "", output_dir: str = "") -> str:
    """Follow a user on Bluesky
    
    Args:
        handle: User handle or DID to follow
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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_follow command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_follow unexpected error: {str(e)}")
        raise RuntimeError(str(e))

@mcp.tool()
def ssky_unfollow(handle: str, delimiter: str = "", output_dir: str = "") -> str:
    """Unfollow a user on Bluesky
    
    Args:
        handle: User handle or DID to unfollow
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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_unfollow command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_unfollow unexpected error: {str(e)}")
        raise RuntimeError(str(e))

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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_repost command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_repost unexpected error: {str(e)}")
        raise RuntimeError(str(e))

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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_unrepost command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_unrepost unexpected error: {str(e)}")
        raise RuntimeError(str(e))

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
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        logger.error(f"ssky_delete command timed out: {' '.join(args)}")
        raise RuntimeError("Command timed out")
    except Exception as e:
        logger.error(f"ssky_delete unexpected error: {str(e)}")
        raise RuntimeError(str(e))

if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass 