from .processor import SubtitleProcessor
from .parser import SRTParser
from .validator import SubtitleValidator

# Create singleton instance
subtitle_processor = SubtitleProcessor()
srt_parser         = SRTParser()
subtitle_validator = SubtitleValidator()


__all__ = [
    # Instances
    "subtitle_processor",
    "srt_parser",
    "subtitle_validator",

    # Classes Models
    "SubtitleProcessor",
    "SRTParser",
    "SubtitleValidator"
]