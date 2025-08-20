from typing import Union

import opik

from application.core.logging import get_logger

logger = get_logger(__name__)


class Prompt:
    def __init__(self, name: str, prompt: str) -> None:
        self.name = name
        self.__prompt: Union[str, "opik.Prompt"] = prompt

        try:
            self.__prompt = opik.Prompt(name=name, prompt=prompt)
        except Exception as e:
            logger.warning(
                f"Can't use Opik to version the prompt (probably due to missing or invalid credentials): {e}"
            )

    @property
    def prompt(self) -> str:
        return getattr(self.__prompt, 'prompt', self.__prompt)

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return self.__str__()


DECIDER_PROMPT = Prompt(
    name="decider_prompt",
    prompt="""
    You are Moovio’s final arbiter. Decide if any candidate scene matches the user’s current transcript.

    Context you MUST use:
    - transcript_text (ASR; may contain minor errors):
    {transcript}
    - observed_actor_names (may be noisy, lowercase):
    {actors}
    
    How to compare:
    1. Prioritize semantic & lexical overlap between transcript_text and each candidate.page_content.
       - Look for distinctive phrases, names, numbers, and bigrams (e.g., “thousandth of a second”, “he won”, names, places).
       - Be tolerant of small ASR glitches and near-homophones (e.g., jann/jan/jane).
    2. Use actor evidence only as a tie-breaker:
       - If candidate.metadata.matched_cast exists, more matched names ⇒ stronger tie-break.
       - If matched_cast is absent, do not infer cast from thin air.
    3. Prefer candidates whose page_content matches the transcript theme and wording more closely than others.
    
    Decision policy:
    - If exactly one candidate clearly fits the transcript, return a match with its media type and id:
      - movie ⇒ use candidate.metadata.movie_id
      - tv     ⇒ use candidate.metadata.tv_show_id
    - If the evidence is promising but not decisive (close contenders or partial overlap), set requery=true (end=false).
    - If nothing meaningfully matches the transcript (generic chatter or mismatched topics), set end=true (requery=false).
    - Never invent IDs or titles. Do not select a match if the page_content does not actually align with the transcript.
    
    Determinism & brevity:
    - Be decisive, deterministic, and concise. No extra commentary; only produce the structured fields requested by the tool.
    """
)

DECIDER_INVOKE_PROMPT = Prompt(
    name="decider_invoke_prompt",
    prompt="""
    {candidates}

    Evaluate each candidate against the system instructions and return the structured result.
    """
)