import re
from typing import List

from config import get_logger

logger = get_logger(__name__)


class SubtitleValidator:
    """Validator for subtitle content."""
    
    def validate(self, srt_content: str) -> None:
        """Validate SRT content."""
        if not srt_content or not isinstance(srt_content, str):
            raise ValueError("SRT content must be a non-empty string")
            
        if len(srt_content.strip()) == 0:
            raise ValueError("SRT content cannot be empty or contain only whitespace")
            
        # Check for basic SRT structure
        lines = srt_content.split('\n')
        if len(lines) < 3:  # Minimum SRT entry: number, timestamp, text
            raise ValueError("SRT content must contain at least one complete subtitle entry")
            
        # Validate timestamp format
        timestamp_pattern = r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}'
        has_timestamp = any(
            re.match(timestamp_pattern, line.strip())
            for line in lines
        )
        if not has_timestamp:
            raise ValueError("SRT content must contain valid timestamps")
    
    def validate_chunks(self, chunks: List[str]) -> None:
        """Validate subtitle chunks."""
        if not chunks:
            raise ValueError("No chunks to validate")
            
        for i, chunk in enumerate(chunks):
            if not chunk or not isinstance(chunk, str):
                raise ValueError(f"Invalid chunk at index {i}: must be a non-empty string")
                
            if len(chunk.strip()) == 0:
                raise ValueError(f"Empty chunk at index {i}")
                
            # TODO: For example, maximum chunk length, content type, etc.