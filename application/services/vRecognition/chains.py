from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from application.core.config import settings
from application.services.vRecognition.prompts import DECIDER_PROMPT, DECIDER_INVOKE_PROMPT


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

def get_ai_decider_chain():
    model = _get_chat_model()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", DECIDER_PROMPT.prompt),      # uses {transcript} and {actors}
            ("human", DECIDER_INVOKE_PROMPT.prompt) # uses {candidates}
        ]
    )

    return prompt | model.with_structured_output(DeciderLLMOutput)
