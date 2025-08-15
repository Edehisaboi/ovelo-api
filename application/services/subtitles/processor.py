from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from application.models.media import TranscriptChunk
from application.core.config import settings
from application.core.logging import get_logger

from .parser import SRTParser
from .validator import SubtitleValidator

logger = get_logger(__name__)


_SENTENCE_REGEX = r'(?:[.!?]|…|。|！|？)(?:["\')\]]*)\s+(?=[A-Z"“(])'

_separators = [
    _SENTENCE_REGEX,        # sentence boundary (no lookbehind)
    r'\n{2,}',
    r'\n',
    r'\s{2,}',
    r'\s+',
    ''
]


class SubtitleProcessor:

    def __init__(self):
        self._parser = SRTParser()
        self._validator = SubtitleValidator()

        self._chunker = RecursiveCharacterTextSplitter\
        .from_tiktoken_encoder(
            encoding_name=settings.OPENAI_TOKEN_ENCODING,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=int(settings.CHUNK_SIZE * settings.CHUNK_OVERLAP_PERCENT),
            separators=_separators,
            is_separator_regex=True,
            keep_separator="end"
        )

    def process(self, srt_content: str) -> List[TranscriptChunk]:
        """End-to-end pipeline: Parse, chunk, merge, enforce token limit, apply overlap, and validate.
        Returns a list of TranscriptChunk objects."""
        try:
            self._validator.validate(srt_content)

            cleaned_lines = self._parser.parse_srt(srt_content)
            if not cleaned_lines:
                raise ValueError("No valid subtitle lines found after parsing.")

            full_text = " ".join(cleaned_lines)
            chunks = self._chunker.split_text(full_text)
            if not chunks:
                raise ValueError("No chunks produced from subtitle content.")

            self._validator.validate_chunks(chunks)

            return [
                TranscriptChunk(
                    index=i,
                    text=chunk.strip().lower(),
                    embedding=None  # To be set later
                )
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            logger.error(f"Error processing subtitle chunks: {str(e)}")
            raise

    def process_file(self, file_path: str, encoding: str = 'utf-8') -> List[TranscriptChunk]:
        """End-to-end pipeline for processing subtitle files from disk."""
        try:
            cleaned_lines = self._parser.parse_srt_file(file_path, encoding)
            if not cleaned_lines:
                raise ValueError("No valid subtitle lines found after parsing file.")

            full_text = " ".join(cleaned_lines)
            return self.process(full_text)
        except Exception as e:
            logger.error(f"Error processing subtitle file chunks: {str(e)}")
            raise


# Create singleton instance
subtitle_processor = SubtitleProcessor()