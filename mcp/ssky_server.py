#!/usr/bin/env python3
"""
Official MCP SDK implementation for ssky (Simple Bluesky Client)
"""

import subprocess
from mcp.server.fastmcp import FastMCP

# Create FastMCP server
mcp = FastMCP("ssky")

@mcp.tool()
def ssky_get(
    param: str = "", 
    limit: int = 25, 
    output_format: str = "long",
    delimiter: str = "",
    output_dir: str = ""
) -> str:
    """Get posts from Bluesky timeline or specific user
    
    Args:
        param: URI(at://...), DID(did:...), handle, or none for timeline
        limit: Number of posts to retrieve (default: 25, same as ssky command)
        output_format: Output format - "text", "json", "long", "id" (default: "long" for AI readability)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "get"]
    
    # Add limit option
    args.extend(["-N", str(limit)])
    
    # Add output format option
    if output_format == "json":
        args.append("-J")
    elif output_format == "long":
        args.append("-L")
    elif output_format == "id":
        args.append("-I")
    elif output_format == "text":
        args.append("-T")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()  
def ssky_post(
    message: str = "", 
    dry_run: bool = False, 
    images: str = "", 
    quote_uri: str = "", 
    reply_to_uri: str = "", 
    output_format: str = "text", 
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
        output_format: Output format - "text", "json", "long", "id" (default: "text")
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
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_search(
    query: str, 
    limit: int = 25, 
    author: str = "", 
    since: str = "", 
    until: str = "", 
    output_format: str = "long", 
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
        output_format: Output format - "text", "json", "long", "id" (default: "long" for AI readability)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "search", query, "--limit", str(limit)]
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_profile(handle: str, output_format: str = "long", delimiter: str = "", output_dir: str = "") -> str:
    """Show user profile information
    
    Args:
        handle: User handle (e.g., user.bsky.social)
        output_format: Output format - "text", "json", "long", "id" (default: "long" for AI readability)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "profile", handle]
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_user(query: str, limit: int = 25, output_format: str = "long", delimiter: str = "", output_dir: str = "") -> str:
    """Search users on Bluesky
    
    Args:
        query: Search query for users
        limit: Number of results to return (default: 25, same as ssky command)
        output_format: Output format - "text", "json", "long", "id" (default: "long" for AI readability)
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "user", query, "--limit", str(limit)]
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_follow(handle: str, output_format: str = "text", delimiter: str = "", output_dir: str = "") -> str:
    """Follow a user on Bluesky
    
    Args:
        handle: User handle or DID to follow
        output_format: Output format - "text", "json", "long", "id" (default: "text")
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "follow", handle]
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_unfollow(handle: str, output_format: str = "text", delimiter: str = "", output_dir: str = "") -> str:
    """Unfollow a user on Bluesky
    
    Args:
        handle: User handle or DID to unfollow
        output_format: Output format - "text", "json", "long", "id" (default: "text")
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "unfollow", handle]
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_repost(post_uri: str, output_format: str = "text", delimiter: str = "", output_dir: str = "") -> str:
    """Repost a post on Bluesky
    
    Args:
        post_uri: URI of the post to repost (at://...)
        output_format: Output format - "text", "json", "long", "id" (default: "text")
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "repost", post_uri]
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_unrepost(post_uri: str, output_format: str = "text", delimiter: str = "", output_dir: str = "") -> str:
    """Unrepost (remove repost) a post on Bluesky
    
    Args:
        post_uri: URI of the post to unrepost (at://...)
        output_format: Output format - "text", "json", "long", "id" (default: "text")
        delimiter: Custom delimiter string
        output_dir: Output to files in specified directory
    """
    args = ["ssky", "unrepost", post_uri]
    
    # Add output format option
    if output_format == "json":
        args.append("--json")
    elif output_format == "long":
        args.append("--long")
    elif output_format == "id":
        args.append("--id")
    elif output_format == "text":
        args.append("--text")
    
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
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ssky_delete(post_uri: str) -> str:
    """Delete a post on Bluesky
    
    Args:
        post_uri: URI of the post to delete (at://...)
    """
    args = ["ssky", "delete", post_uri]
    
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip() if result.stdout.strip() else "Post deleted successfully"
        else:
            return f"Error: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass 