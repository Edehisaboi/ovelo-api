import re
import unicodedata
from typing import List, Tuple, Iterable
from datetime import timedelta

import srt  # pip install srt
from spellchecker import SpellChecker


class SRTParser:

    def __init__(self):
        # Keep your formatting + cue clean-up patterns
        self.formatting_tags_pattern = re.compile(r'<[^>]+>')
        self.sound_effects_pattern = re.compile(r'[\[(](.*?)[)\]]')

        self.music_line_pattern = re.compile(
            r'^\s*('
            r'\[[^]]*music[^]]*\]|'   # [ ... music ... ]
            r'\([^)]*music[^)]*\)|'   # ( ... music ... )
            r'\[[^]]*song[^]]*\]|'    # [ ... song ... ]
            r'<i>.*?♪.*?</i>|'        # <i> ... ♪ ... </i>
            r'^♪.*♪$|^♪|♪$'           # lines of music notes
            r')',
            re.IGNORECASE
        )
        self.lyric_line_pattern = re.compile(r'♪')
        self.only_lyrics_pattern = re.compile(r'^<i>.*?♪.*?</i>$')

        self.spell_checker = SpellChecker()

    @staticmethod
    def _normalize_text(text: str) -> str:
        # Handles fullwidth punctuation etc. (pairs well with srt’s wide timestamp support)
        return unicodedata.normalize("NFKC", text)

    def _is_music_line(self, text: str) -> bool:
        if self.music_line_pattern.search(text):
            return True
        if self.only_lyrics_pattern.match(text):
            return True
        if self.lyric_line_pattern.search(text) and len(re.sub(r'[^♪a-zA-Z0-9]', '', text)) < 12:
            return True
        return False

    def _correct_spelling(self, text: str) -> str:
        words, out = text.split(), []
        for w in words:
            if w.isalpha() and w not in self.spell_checker:
                corr = self.spell_checker.correction(w)
                out.append(corr if corr else w)
            else:
                out.append(w)
        return ' '.join(out)

    def _clean_text(self, text: str, remove_punct: bool = True, correct_spelling: bool = True) -> str:
        text = self._normalize_text(text)
        text = re.sub(r"\{.*?}", "", text)               # remove {…}
        text = self.formatting_tags_pattern.sub('', text)
        text = self.sound_effects_pattern.sub('', text)         # remove [ … ] / ( … )
        text = text.replace('*', '')
        text = re.sub(r"^\s*-\s*", "", text)             # leading dash
        if remove_punct:
            text = text.replace('...', ',').replace('-', '')
        text = ' '.join(text.split())
        if correct_spelling:
            text = self._correct_spelling(text)
        return text.strip()

    def _iter_dialogue_texts(
        self,
        srt_content: str,
        remove_music: bool = True,
        ignore_errors: bool = True
    ) -> Iterable[str]:
        """Yields cleaned dialogue strings, one per subtitle cue"""
        # Robust parse (handles odd delimiters, missing ms, CRLF, missing blank line, etc.)
        subs = list(srt.parse(srt_content, ignore_errors=ignore_errors))

        # Sort, drop invalid/empty cues (start>=end, negative start, empty content)
        subs = list(srt.sort_and_reindex(subs, skip=True))

        for sub in subs:
            # Normalize internal newlines within a cue to spaces
            raw = sub.content.replace("\r\n", "\n").replace("\r", "\n")
            raw = " ".join(part.strip() for part in raw.split("\n") if part.strip())

            if remove_music and self._is_music_line(raw):
                continue

            cleaned = self._clean_text(raw)
            if cleaned:
                yield cleaned

    def parse_srt(
        self,
        srt_content: str,
        remove_music: bool = True,
        ignore_errors: bool = True
    ) -> List[str]:
        """Returns reconstructed sentences/paragraphs, cleaned."""
        dialogue_lines = list(self._iter_dialogue_texts(
            srt_content, remove_music=remove_music, ignore_errors=ignore_errors
        ))

        sentences: List[str] = []
        buf = ""
        for i, line in enumerate(dialogue_lines):
            buf = (buf + " " + line).strip() if buf else line
            next_line = dialogue_lines[i + 1] if i + 1 < len(dialogue_lines) else ""
            ends_with_sentence = re.search(r'[.!?]["\']?$', line)
            next_is_new_sentence = bool(next_line and next_line.strip() and next_line.strip()[0].isupper())
            next_is_empty = not bool(next_line.strip())
            if ends_with_sentence and (next_is_new_sentence or next_is_empty):
                sentences.append(buf)
                buf = ""
        if buf:
            sentences.append(buf)
        return sentences

    def parse_srt_file(self, file_path: str, encoding: str = 'utf-8') -> List[str]:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return self.parse_srt(content)
        except Exception as e:
            raise Exception(f"Error parsing SRT file: {str(e)}")

    def parse_srt_with_times(
        self,
        srt_content: str,
        remove_music: bool = True,
        ignore_errors: bool = True
    ) -> List[Tuple[str, timedelta, timedelta]]:
        """
        Returns a list of (clean_text, start, end) tuples per cue.
        Useful if you need alignment to audio/video later.
        """
        subs = list(srt.sort_and_reindex(
            srt.parse(srt_content, ignore_errors=ignore_errors),
            skip=True
        ))
        out: List[Tuple[str, timedelta, timedelta]] = []
        for sub in subs:
            raw = " ".join(part.strip() for part in sub.content.replace("\r\n", "\n").split("\n") if part.strip())
            if remove_music and self._is_music_line(raw):
                continue
            cleaned = self._clean_text(raw)
            if cleaned:
                out.append((cleaned, sub.start, sub.end))
        return out
