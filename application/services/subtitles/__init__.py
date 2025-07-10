from .processor import SubtitleProcessor
from .parser import SRTParser
from .validator import SubtitleValidator

# Create singleton instance
subtitle_processor = SubtitleProcessor()
subtitle_validator = SubtitleValidator()
srt_parser         = SRTParser()


__all__ = [
    # Instances
    "subtitle_processor",
    "subtitle_validator",
    "srt_parser",

    # Classes Models
    "SubtitleProcessor",
    "SRTParser",
    "SubtitleValidator"
]