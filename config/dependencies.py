import httpx
from openai import OpenAI
from fastapi import Depends
from config import Settings
from functools import lru_cache
from api.services.subtitle import opensubtitles_client


@lru_cache()
def get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


@lru_cache()
def get_opensubtitles_client():
    """Get the singleton OpenSubtitles client instance."""
    return opensubtitles_client


@lru_cache()
def get_openai_client():
    return OpenAI(api_key=Settings.OPENAI_API_KEY)