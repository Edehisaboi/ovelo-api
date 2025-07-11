from typing import List

import tiktoken

from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter

from application.models.media import TranscriptChunk
from application.core.config import settings
from application.core.logging import get_logger
from application.core.resources import embedding_client

from .parser import SRTParser
from .validator import SubtitleValidator

logger = get_logger(__name__)


class SubtitleProcessor:
    """
    Processes subtitle (SRT) content into semantically meaningful, overlapped, and size-controlled chunks.

    This function implements a robust pipeline for parsing, cleaning, and segmenting SRT subtitle content into coherent chunks suitable for downstream tasks such as vector search or embedding generation.
    It ensures context continuity, enforces token limits, and validates input/output.

    Returns:
        List[TranscriptChunk]: A list of TranscriptChunk dataclass instances, each containing a semantically coherent chunk of subtitle text, ready for embedding or further processing.

    Pipeline Steps:
        1. **Parsing & Cleaning**: Utilizes SRTParser to parse and normalize subtitle lines, removing formatting issues and inconsistencies.
        2. **Semantic Chunking**: Employs SemanticChunker with an embedding-based approach to group text into context-rich, coherent segments.
        3. **Small Chunk Merging**: Merges chunks with fewer than `min_chunk_words` words with adjacent chunks to ensure sufficient information density.
        4. **Token Limit Enforcement**: Splits oversized chunks exceeding `max_token_size` using RecursiveCharacterTextSplitter with OpenAI’s tiktoken encoder.
        5. **Percentage Overlap**: Applies overlap between adjacent chunks based on `overlap_percentage` to enhance robustness for search/retrieval tasks.
        6. **Validation**: Validates input SRT content and output chunks using SubtitleValidator to ensure correctness and consistency.

    Notes:
        - The pipeline is optimized for downstream vector search, ensuring chunks are neither too long (to avoid model errors) nor too short (to maintain context).
        - Overlap enhances retrieval performance for short queries by preserving contextual continuity across chunk boundaries.
        """

    def __init__(self):
        self._parser = SRTParser()
        self._validator = SubtitleValidator()
        self._min_chunk_words = settings.MIN_CHUNK_WORDS

        self._chunker = SemanticChunker(
            embeddings=embedding_client.embeddings,
            buffer_size=settings.CHUNK_BUFFER_SIZE,
            breakpoint_threshold_type=settings.CHUNK_BREAKPOINT_TYPE,
            breakpoint_threshold_amount=settings.CHUNK_BREAKPOINT_AMOUNT,
            min_chunk_size=None  # Minimum chunk size is enforced post-merge
        )

    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text semantically and merge small chunks to ensure minimum word count per chunk.
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
                    if len(buffer.split()) < min_words or len(chunk_words) < min_words:
                        buffer = f"{buffer} {chunk}".strip()
                    else:
                        merged_chunks.append(buffer)
                        buffer = chunk
                else:
                    buffer = chunk

            if buffer:
                merged_chunks.append(buffer)

            if len(merged_chunks) > 1 and len(merged_chunks[-1].split()) < min_words:
                merged_chunks[-2] = f"{merged_chunks[-2]} {merged_chunks[-1]}".strip()
                merged_chunks.pop()

            return merged_chunks

        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise

    @staticmethod
    def _enforce_token_limit_with_rcts(
        chunks: List[str],
        token_limit: int = settings.CHUNK_SIZE
    ) -> List[str]:
        """
        Ensures each chunk does not exceed the allowed token limit for the embedding model.
        Oversized chunks are split using RecursiveCharacterTextSplitter (tiktoken-based).
        """
        encoding = tiktoken.get_encoding(settings.OPENAI_TOKEN_ENCODING)
        rcts = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name=settings.OPENAI_TOKEN_ENCODING,
            chunk_size=token_limit
        )
        final_chunks = []
        for chunk in chunks:
            tokens = encoding.encode(chunk)
            if len(tokens) <= token_limit:
                final_chunks.append(chunk)
            else:
                # Split and flatten output
                subchunks = rcts.split_text(chunk)
                final_chunks.extend(subchunks)
        return final_chunks

    @staticmethod
    def _overlap_chunks_by_percent(
        chunks: List[str],
        overlap_pct: float = settings.CHUNK_OVERLAP_PERCENT
    ) -> List[str]:
        """
        Adds N% overlap (by word count) between adjacent chunks for better retrieval recall.
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
        End-to-end pipeline: Parse, chunk, merge, enforce token limit, apply overlap, and validate.
        Returns a list of TranscriptChunk objects.
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

            # Step 1: Enforce max token size
            chunks = self._enforce_token_limit_with_rcts(chunks)

            # Step 2: Apply percentage overlap
            overlapped_chunks = self._overlap_chunks_by_percent(chunks, settings.CHUNK_OVERLAP_PERCENT)

            # Optionally print debug info
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
        End-to-end pipeline for processing subtitle files from disk.
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
