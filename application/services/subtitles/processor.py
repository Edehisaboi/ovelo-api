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
    """Process and chunk subtitle content into semantically meaningful, overlapped chunks."""
    def __init__(self):
        self._parser = SRTParser()
        self._validator = SubtitleValidator()
        self._min_chunk_words = settings.MIN_CHUNK_WORDS

        self._chunker = SemanticChunker(
            embeddings=embedding_client.embeddings,
            buffer_size=settings.CHUNK_BUFFER_SIZE,
            breakpoint_threshold_type=settings.CHUNK_BREAKPOINT_TYPE,
            breakpoint_threshold_amount=settings.CHUNK_BREAKPOINT_AMOUNT,
            min_chunk_size=None  # Post-merge handles minimum chunk size.
        )

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into semantic chunks and merge short chunks with neighbors.
        """
        try:
            chunks = [chunk.strip() for chunk in self._chunker.split_text(text)]
            min_words = self._min_chunk_words
            if not chunks:
                return []

            merged_chunks = []
            buffer = ""

            for chunk in chunks:
                chunk_words = chunk.split()
                if buffer:
                    # Merge if either buffer or current chunk is too small
                    if len(buffer.split()) < min_words or len(chunk_words) < min_words:
                        buffer = f"{buffer} {chunk}".strip()
                    else:
                        merged_chunks.append(buffer)
                        buffer = chunk
                else:
                    buffer = chunk

            if buffer:
                merged_chunks.append(buffer)

            # If the last chunk is too small, merge it backward
            if len(merged_chunks) > 1 and len(merged_chunks[-1].split()) < min_words:
                merged_chunks[-2] = f"{merged_chunks[-2]} {merged_chunks[-1]}".strip()
                merged_chunks.pop()

            return merged_chunks

        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise

    @staticmethod
    def _overlap_chunks_by_percent(
        chunks: List[str], overlap_pct: float = settings.CHUNK_OVERLAP_PERCENT
    ) -> List[str]:
        """
        Add N% overlap (by word count) between adjacent chunks.
        overlap_pct should be a float in [0, 1).
        """
        if not (0 <= overlap_pct < 1):
            raise ValueError("overlap_pct must be between 0 (inclusive) and 1 (exclusive)")
        if not chunks:
            return []

        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_words = overlapped[-1].split()
            curr_words = chunks[i].split()
            overlap_n = max(1, int(len(prev_words) * overlap_pct))
            overlap_words = prev_words[-overlap_n:] if overlap_n < len(prev_words) else prev_words
            new_chunk = " ".join(overlap_words + curr_words)
            overlapped.append(new_chunk)
        return overlapped

    def process(self, srt_content: str) -> List[TranscriptChunk]:
        """
        Process SRT content and split it into semantically meaningful, overlapped chunks.
        """
        try:
            self._validator.validate(srt_content)
            cleaned_lines = self._parser.parse_srt(srt_content)

            if not cleaned_lines:
                raise ValueError("No valid subtitle lines found after parsing.")

            full_text = " ".join(cleaned_lines)
            chunks = self._chunk_text(full_text)

            if not chunks:
                raise ValueError("No semantic chunks produced from subtitle content.")

            # Apply overlap
            overlapped_chunks = self._overlap_chunks_by_percent(chunks, settings.CHUNK_OVERLAP_PERCENT)

            print("\n\n DEBUG: Chunks after initial processing:")
            for i, chunk in enumerate(overlapped_chunks):
                print(f"Chunk {i}:\n{chunk}\n")

            self._validator.validate_chunks(overlapped_chunks)

            return [
                TranscriptChunk(
                    index=i,
                    text=chunk,
                    embedding=None  # To be set later
                )
                for i, chunk in enumerate(overlapped_chunks)
            ]

        except Exception as e:
            logger.error(f"Error processing subtitle chunks: {str(e)}")
            raise

    def process_file(self, file_path: str, encoding: str = 'utf-8') -> List[TranscriptChunk]:
        """
        Process an SRT file and split it into semantic, overlapped chunks.
        """
        try:
            cleaned_lines = self._parser.parse_srt_file(file_path, encoding)

            if not cleaned_lines:
                raise ValueError("No valid subtitle lines found after parsing file.")

            full_text = " ".join(cleaned_lines)
            return self.process(full_text)

        except Exception as e:
            logger.error(f"Error processing subtitle file chunks: {str(e)}")
            raise
