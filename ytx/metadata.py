"""Utilities for extracting video ID and processing metadata."""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Video ID string, or None if not found
    """
    # Handle various YouTube URL formats:
    # - https://www.youtube.com/watch?v=VIDEO_ID
    # - https://youtu.be/VIDEO_ID
    # - https://www.youtube.com/embed/VIDEO_ID
    # - https://m.youtube.com/watch?v=VIDEO_ID
    
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def sanitize_title(title: str, max_length: int = 80) -> str:
    """Sanitize video title for use in filesystem.
    
    Args:
        title: Raw video title
        max_length: Maximum length of sanitized title
        
    Returns:
        Sanitized title suitable for filesystem use
    """
    # Convert to lowercase
    sanitized = title.lower()
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    
    # Remove unsafe characters (keep only alphanumeric, underscore, hyphen)
    sanitized = re.sub(r"[^a-z0-9_-]", "", sanitized)
    
    # Remove consecutive underscores/hyphens
    sanitized = re.sub(r"[_-]+", "_", sanitized)
    
    # Trim underscores/hyphens from start and end
    sanitized = sanitized.strip("_-")
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip("_-")
    
    return sanitized if sanitized else "video"


def load_metadata_from_file(meta_json_path: Path) -> Dict[str, Any]:
    """Load metadata from meta.json file.
    
    Args:
        meta_json_path: Path to meta.json file
        
    Returns:
        Metadata dictionary
    """
    with meta_json_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def generate_output_folder_name(metadata: Dict[str, Any], run_date: str) -> str:
    """Generate output folder name in format: YYYY-MM-DD__sanitized-title__video-id
    
    Args:
        metadata: Video metadata dictionary
        run_date: Run date in YYYY-MM-DD format
        
    Returns:
        Folder name string
    """
    title = metadata.get("title", "untitled")
    video_id = metadata.get("id", metadata.get("video_id", "unknown"))
    
    sanitized = sanitize_title(title)
    
    return f"{run_date}__{sanitized}__{video_id}"
