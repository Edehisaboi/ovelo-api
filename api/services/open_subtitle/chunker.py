from typing import List
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from api.services.tmdb import TranscriptChunk
from config import Settings, get_logger
from .srt_parser import SRTParser

logger = get_logger(__name__)

class SubtitleChunker:
    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self.parser = SRTParser()
        
        # Initialize the semantic chunker with OpenAI embeddings
        self.chunker = SemanticChunker(
            OpenAIEmbeddings(),
            breakpoint_threshold_type=self.settings.CHUNK_BREAKPOINT_TYPE,
            breakpoint_threshold_amount=self.settings.CHUNK_BREAKPOINT_AMOUNT,
            number_of_chunks=self.settings.CHUNK_SIZE
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into semantic chunks.
        
        Args:
            text (str): The text to split into chunks
            
        Returns:
            List[str]: List of text chunks
        """
        try:
            return self.chunker.split_text(text)
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise

    def chunk_subtitle(self, srt_content: str) -> List[TranscriptChunk]:
        """
        Process SRT content and split it into semantic chunks.
        
        Args:
            srt_content (str): The SRT file content
            
        Returns:
            List[TranscriptChunk]: List of chunks with metadata
        """
        try:
            # Parse and clean the SRT content
            cleaned_lines = self.parser.parse_srt(srt_content)
            
            # Join lines into a single text
            full_text = " ".join(cleaned_lines)
            
            # Split into chunks
            chunks = self.chunk_text(full_text)
            
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

    def chunk_subtitle_file(self, file_path: str, encoding: str = 'utf-8') -> List[TranscriptChunk]:
        """
        Process an SRT file and split it into semantic chunks.
        
        Args:
            file_path (str): Path to the SRT file
            encoding (str): File encoding (default: 'utf-8')
            
        Returns:
            List[TranscriptChunk]: List of chunks with metadata
        """
        try:
            # Read and parse the SRT file
            cleaned_lines = self.parser.parse_srt_file(file_path, encoding)
            
            # Join lines into a single text
            full_text = " ".join(cleaned_lines)
            
            # Split into chunks
            chunks = self.chunk_text(full_text)
            
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
            logger.error(f"Error processing subtitle file chunks: {str(e)}")
            raise
