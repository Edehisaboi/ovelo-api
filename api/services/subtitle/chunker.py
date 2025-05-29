from typing import List
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from api.services.tmdb import TranscriptChunk
from config import Settings, get_logger
from ..open_subtitle.srt_parser import SRTParser
from .validator import SubtitleValidator

logger = get_logger(__name__)


class SubtitleProcessor:
    """Process and chunk subtitle content."""
    
    def __init__(self):
        self._parser = SRTParser()
        self._validator = SubtitleValidator()
        self._chunker = SemanticChunker(
            OpenAIEmbeddings(),
            breakpoint_threshold_type=Settings.CHUNK_BREAKPOINT_TYPE,
            breakpoint_threshold_amount=Settings.CHUNK_BREAKPOINT_AMOUNT,
            number_of_chunks=Settings.CHUNK_SIZE
        )
    
    def _chunk_text(
        self,
        text: str
    ) -> List[str]:
        """Split text into semantic chunks."""
        try:
            return self._chunker.split_text(text)
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def process(
        self,
        srt_content: str
    ) -> List[TranscriptChunk]:
        """Process SRT content and split it into semantic chunks."""
        try:
            # Validate input
            self._validator.validate(srt_content)
            
            # Parse and clean the SRT content
            cleaned_lines = self._parser.parse_srt(srt_content)
            
            # Validate cleaned lines
            if not cleaned_lines:
                raise ValueError("No valid subtitle lines found after parsing")
            
            # Join lines into a single text
            full_text = " ".join(cleaned_lines)
            
            # Split into chunks
            chunks = self._chunk_text(full_text)
            
            # Validate chunks
            self._validator.validate_chunks(chunks)
            
            # Add metadata to each chunk
            chunked_subtitles = []
            for i, chunk in enumerate(chunks):
                chunked_subtitles.append(
                    TranscriptChunk(
                        index=i,
                        text=chunk
                    )
                )
            
            return chunked_subtitles
            
        except Exception as e:
            logger.error(f"Error processing subtitle chunks: {str(e)}")
            raise
    
    def process_file(
        self,
        file_path: str,
        encoding: str = 'utf-8'
    ) -> List[TranscriptChunk]:
        """Process an SRT file and split it into semantic chunks."""
        try:
            # Read and parse the SRT file
            cleaned_lines = self._parser.parse_srt_file(file_path, encoding)
            
            # Join lines into a single text
            full_text = " ".join(cleaned_lines)
            
            # Process the text
            return self.process(full_text)
            
        except Exception as e:
            logger.error(f"Error processing subtitle file chunks: {str(e)}")
            raise 