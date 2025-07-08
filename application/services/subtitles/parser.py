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

    def _correct_spelling(
            self,text: str
    ) -> str:
        """Correct spelling in a text string."""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip words that are already correct or contain numbers/special characters
            if word.isalpha() and word not in self.spell_checker:
                correction = self.spell_checker.correction(word)
                corrected_words.append(correction if correction else word)
            else:
                corrected_words.append(word)
                
        return ' '.join(corrected_words)

    def _clean_text(
            self,
            text:               str,
            remove_punct:       bool = True,
            correct_spelling:   bool = True
    ) -> str:
        """Clean a single line of subtitle text."""
        text = self._normalize_text(text)
        text = self.formatting_tags_pattern.sub('', text)
        text = self.sound_effects_pattern.sub('', text)
        text = text.replace('*', '')

        if remove_punct:
            text = text.replace('...', ',').replace('-', '')

        text = ' '.join(text.split())  # remove extra whitespace
        text = text.lower()
        
        if correct_spelling:
            text = self._correct_spelling(text)
            
        return text.strip()

    def parse_srt(
            self,
            srt_content: str
    ) -> List[str]:
        """Parse SRT content and return list of cleaned subtitle lines."""
        lines = srt_content.split('\n')
        cleaned_lines = []
        current_text = []

        for line in lines:
            line = line.strip()

            if not line:
                if current_text:
                    cleaned_lines.append(' '.join(current_text))
                    current_text = []
                continue

            if self.line_number_pattern.match(line) or self.timestamp_pattern.match(line):
                continue

            cleaned_line = self._clean_text(line)
            if cleaned_line:
                current_text.append(cleaned_line)

        if current_text:
            cleaned_lines.append(' '.join(current_text))

        return cleaned_lines

    def parse_srt_file(
            self,
            file_path:  str,
            encoding:   str = 'utf-8'
    ) -> List[str]:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return self.parse_srt(content)
        except Exception as e:
            raise Exception(f"Error parsing SRT file: {str(e)}") 