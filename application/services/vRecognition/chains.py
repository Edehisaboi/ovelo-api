from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from application.core.config import settings
from application.services.vRecognition.prompts import DECIDER_PROMPT_TEMPLATE, DECIDER_INVOKE_PROMPT_TEMPLATE


class Match(BaseModel):
    type: Literal["movie", "tv"]
    id:   str

class DeciderLLMOutput(BaseModel):
    requery: bool = Field(
        default=False,
        description="Whether to re-query the graph if the match is not clear.",
    )
    end: bool = Field(
        default=False,
        description="No possible match found, end the session.",
    )
    match: Optional[Match] = None


def _get_chat_model(
    temperature: float = settings.LLM_TEMPERATURE,
    model_name: str = settings.OPENAI_LLM_MODEL,
) -> ChatOpenAI:
    return ChatOpenAI(api_key=SecretStr(settings.OPENAI_API_KEY), model=model_name, temperature=temperature)

def get_ai_decider_chain(transcript: str, actors: str, candidates: str):
    model = _get_chat_model()
    system_prompt = SystemMessagePromptTemplate(
        prompt=DECIDER_PROMPT_TEMPLATE.partial(
            transcript=transcript,
            actors=actors,
        )
    )
    invoke_prompt = HumanMessagePromptTemplate(
        prompt=DECIDER_INVOKE_PROMPT_TEMPLATE.partial(candidates=candidates)
    )

    prompt = ChatPromptTemplate.from_messages([system_prompt, invoke_prompt])

    return prompt | model.with_structured_output(DeciderLLMOutput)
