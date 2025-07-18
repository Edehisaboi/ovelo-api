import re
import unicodedata
from typing import List

from spellchecker import SpellChecker


class SRTParser:
    """Subtitle (.srt) parser for extracting, cleaning, and reconstructing dialogue,
    with configurable removal of music/lyrics and sound effects lines.
    Provides spell correction, normalization, and chunking into paragraphs."""

    def __init__(self):
        # Matches standard SRT timestamp lines indicating the start and end time for a subtitle block.
        # Example match: "00:01:01,600 --> 00:01:04,200"
        # After: (matched and removed)
        self.timestamp_pattern = re.compile(
            r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}'
        )

        # Matches lines that are just the subtitle sequence/block numbers.
        # Example matches: "1", "25"
        # After: (matched and removed)
        self.line_number_pattern = re.compile(r'^\d+$')

        # Matches all HTML or XML-style formatting tags (e.g., <i>, <b>, </font>) in subtitle lines.
        # Example matches:
        #   "<i>Some text</i>" => "Some text"
        #   "<b>Hello!</b>"    => "Hello!"
        #   "<font color='red'>Warning</font>" => "Warning"
        self.formatting_tags_pattern = re.compile(r'<[^>]+>')

        # Matches non-dialogue cues in square or round brackets, often for sound effects or music.
        # Example matches:
        #   "[music playing] Dramatic scene." => "Dramatic scene."
        #   "(applause)" => ""
        self.sound_effects_pattern = re.compile(r'[\[(](.*?)[)\]]')

        # Matches lines that are:
        # - Music or song cues inside brackets/parentheses
        # - Entire lines of lyrics inside <i>...</i> tags containing ♪
        # - Lines starting/ending with ♪ or consisting entirely of music notes
        # Example matches (all matched and removed):
        #   "[music playing]", "[song by Billie Eilish]", "(soft music)"
        #   "<i>♪ I'm not your friend or anything, damn... ♪</i>"
        #   "♪ La la la la la ♪", "♪"
        self.music_line_pattern = re.compile(
            r'^\s*('
            r'\[[^]]*music[^]]*\]|'  # [ ... music ... ]
            r'\([^)]*music[^)]*\)|'  # ( ... music ... )
            r'\[[^]]*song[^]]*\]|'  # [ ... song ... ]
            r'<i>.*?♪.*?</i>|'  # <i> ... ♪ ... </i>
            r'^♪.*♪$|^♪|♪$'  # lines of music notes
            r')',
            re.IGNORECASE
        )

        # Matches any line containing one or more music notes (♪), often used in subtitles to indicate lyrics.
        # Example matches:
        #   "♪ I want it that way ♪"
        #   "<i>♪ Now watch me whip... ♪</i>"
        #   "I love this song! ♪"
        #   (used to help skip)
        self.lyric_line_pattern = re.compile(r'♪')

        # Matches lines that are ONLY a lyric, entirely inside <i>...</i> tags and contain at least one ♪.
        # Example matches:
        #   "<i>♪ I came all this way just to feel this ♪</i>"
        #   "<i>♪ Hallelujah, baby, light it up ♪</i>"
        #   (matched and removed)
        self.only_lyrics_pattern = re.compile(r'^<i>.*?♪.*?</i>$')

        # Initialize the spell checker (for English-language spell correction)
        self.spell_checker = SpellChecker()

    @staticmethod
    def _normalize_text(text: str) -> str:
        return unicodedata.normalize("NFKC", text)

    def _is_music_line(self, text: str) -> bool:
        # Skip lines that are just music cues or lyrics
        if self.music_line_pattern.search(text):
            return True
        if self.only_lyrics_pattern.match(text):
            return True
        if self.lyric_line_pattern.search(text) and len(re.sub(r'[^♪a-zA-Z0-9]', '', text)) < 12:
            # If mostly music notes and a few words, skip
            return True
        return False

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
        text = re.sub(r"\{.*?}", "", text)  # Remove SRT curly-brace tags
        text = self.formatting_tags_pattern.sub('', text)
        text = self.sound_effects_pattern.sub('', text)
        text = text.replace('*', '')

        # Remove leading dash for dialogue lines
        text = re.sub(r"^\s*-\s*", "", text)

        if remove_punct:
            text = text.replace('...', ',').replace('-', '')
        text = ' '.join(text.split())  # remove extra whitespace
        if correct_spelling:
            text = self._correct_spelling(text)
        return text.strip()

    def parse_srt(self, srt_content: str, remove_music: bool = True) -> List[str]:
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
            if self._is_music_line(line) and remove_music:
                continue
            cleaned_line = self._clean_text(line)
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
