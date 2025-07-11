from typing import List

from langchain_experimental.text_splitter import SemanticChunker

from application.models.media import TranscriptChunk
from application.core.config import settings
from application.core.logging import get_logger
from application.core.resources import embedding_client

from .parser import SRTParser
from .validator import SubtitleValidator

logger = get_logger(__name__)

class SubtitleProcessor:
    """Process and chunk subtitle content into semantically meaningful chunks."""
    def __init__(self):
        self._parser = SRTParser()
        self._validator = SubtitleValidator()
        self._min_chunk_words = settings.MIN_CHUNK_WORDS

        # Set up SemanticChunker with parameters from settings or sensible defaults
        self._chunker = SemanticChunker(
            embeddings=embedding_client.embeddings,
            buffer_size=settings.CHUNK_BUFFER_SIZE,
            breakpoint_threshold_type=settings.CHUNK_BREAKPOINT_TYPE,
            breakpoint_threshold_amount=settings.CHUNK_BREAKPOINT_AMOUNT,
            min_chunk_size=None  # handle minimum chunk length after
        )

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into semantic chunks, merging short ones to neighbors."""
        try:
            chunks = [chunk.strip() for chunk in self._chunker.split_text(text)]
            min_words = self._min_chunk_words

            if not chunks:
                return []

            merged_chunks = []
            buffer = ""

            for i, chunk in enumerate(chunks):
                chunk_words = chunk.split()
                if buffer:
                    # Try to merge with buffer if either is too small
                    if len(buffer.split()) < min_words or len(chunk_words) < min_words:
                        buffer = f"{buffer} {chunk}".strip()
                    else:
                        merged_chunks.append(buffer)
                        buffer = chunk
                else:
                    buffer = chunk

            # Add whatever remains in buffer
            if buffer:
                merged_chunks.append(buffer)

            # If the very last chunk is still too small, merge it backward
            if len(merged_chunks) > 1 and len(merged_chunks[-1].split()) < min_words:
                merged_chunks[-2] = f"{merged_chunks[-2]} {merged_chunks[-1]}".strip()
                merged_chunks.pop()

            return merged_chunks

        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise

    def process(self, srt_content: str) -> List[TranscriptChunk]:
        """Process SRT content and split it into semantic chunks."""
        try:
            # Validate SRT input format
            self._validator.validate(srt_content)

            # Parse and clean the SRT content into sentence-like lines
            cleaned_lines = self._parser.parse_srt(srt_content)

            if not cleaned_lines:
                raise ValueError("No valid subtitle lines found after parsing.")

            # Join lines into a single, space-separated text (to reconstruct paragraphs)
            full_text = " ".join(cleaned_lines)

            # Chunk the reconstructed text
            chunks = self._chunk_text(full_text)

            if not chunks:
                raise ValueError("No semantic chunks produced from subtitle content.")

            print("\n\n DEBUG: Chunks after initial processing:")
            for i, chunk in enumerate(chunks):
                print(f"Chunk {i}: \n {chunk}")

            # Validate final chunks
            self._validator.validate_chunks(chunks)

            # Build the TranscriptChunk list
            chunked_subtitles = [
                TranscriptChunk(
                    index=i,
                    text=chunk,
                    embedding=None  # Embedding will be set in a separate step/service
                )
                for i, chunk in enumerate(chunks)
            ]

            return chunked_subtitles

        except Exception as e:
            logger.error(f"Error processing subtitle chunks: {str(e)}")
            raise

    def process_file(self, file_path: str, encoding: str = 'utf-8') -> List[TranscriptChunk]:
        """Process an SRT file and split it into semantic chunks."""
        try:
            # Parse and clean SRT file into lines
            cleaned_lines = self._parser.parse_srt_file(file_path, encoding)

            if not cleaned_lines:
                raise ValueError("No valid subtitle lines found after parsing file.")

            # Join lines into single text
            full_text = " ".join(cleaned_lines)

            # Process using the main pipeline
            return self.process(full_text)

        except Exception as e:
            logger.error(f"Error processing subtitle file chunks: {str(e)}")
            raise
