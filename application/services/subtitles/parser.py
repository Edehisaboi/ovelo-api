import re
import unicodedata
from typing import List

from spellchecker import SpellChecker


class SRTParser:
    def __init__(self):
        # Regular expressions for matching SRT elements
        self.timestamp_pattern = re.compile(
            r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}'
        )
        self.line_number_pattern = re.compile(r'^\d+$')
        self.formatting_tags_pattern = re.compile(r'<[^>]+>')
        self.sound_effects_pattern = re.compile(r'[\[(](.*?)[\])]')
        self.spell_checker = SpellChecker()

    @staticmethod
    def _normalize_text(text: str) -> str:
        return unicodedata.normalize("NFKC", text)

    def _correct_spelling(self, text: str) -> str:
        words = text.split()
        corrected_words = []
        for word in words:
            if word.isalpha() and word not in self.spell_checker:
                correction = self.spell_checker.correction(word)
                corrected_words.append(correction if correction else word)
            else:
                corrected_words.append(word)
        return ' '.join(corrected_words)

    def _clean_text(self, text: str, remove_punct: bool = True, correct_spelling: bool = True) -> str:
        text = self._normalize_text(text)
        text = self.formatting_tags_pattern.sub('', text)
        text = self.sound_effects_pattern.sub('', text)
        text = text.replace('*', '')
        if remove_punct:
            text = text.replace('...', ',').replace('-', '')
        text = ' '.join(text.split())  # remove extra whitespace
        if correct_spelling:
            text = self._correct_spelling(text)
        return text.strip()

    def parse_srt(self, srt_content: str) -> List[str]:
        """
        Parse SRT content and return a list of reconstructed sentences/paragraphs,
        not just lines. This enables semantically meaningful chunking.
        """
        lines = srt_content.split('\n')
        dialogue_lines = []

        # Step 1: Remove all SRT numbers, timestamps, empty lines. Clean text.
        for line in lines:
            line = line.strip()
            if not line or self.line_number_pattern.match(line) or self.timestamp_pattern.match(line):
                continue
            cleaned_line = self._clean_text(line, remove_punct=False)
            if cleaned_line:
                dialogue_lines.append(cleaned_line)

        # Step 2: Reconstruct sentences/paragraphs
        sentences = []
        buffer = ""
        for i, line in enumerate(dialogue_lines):
            # If buffer is not empty, add a space before new line
            if buffer:
                buffer += " "
            buffer += line

            # Look ahead to decide if this is an end of sentence/paragraph
            next_line = dialogue_lines[i + 1] if i + 1 < len(dialogue_lines) else ""
            next_line_stripped = next_line.strip() if next_line else ""

            # End with period, question mark, exclamation mark, possibly quotes
            ends_with_sentence = re.search(r'[.!?]["\']?$', line)
            next_is_new_sentence = next_line_stripped and next_line_stripped[0].isupper()
            next_is_empty = not next_line_stripped

            # Sentence/paragraph boundary condition
            if ends_with_sentence and (next_is_new_sentence or next_is_empty):
                sentences.append(buffer.strip())
                buffer = ""

        if buffer:
            sentences.append(buffer.strip())

        return sentences

    def parse_srt_file(self, file_path: str, encoding: str = 'utf-8') -> List[str]:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return self.parse_srt(content)
        except Exception as e:
            raise Exception(f"Error parsing SRT file: {str(e)}")
