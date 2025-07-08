from .stt import STTService
from application.models.stt import STTResult, STTMessageType
from application.core.logging import get_logger

logger = get_logger(__name__)

# Create singleton instance
stt_service = STTService()

__all__ = [
    "stt_service",
    "STTService",
    "STTResult",
    "STTMessageType"
]

"""
STT (Speech-to-Text) service module for real-time transcription.
This module provides real-time speech-to-text capabilities using OpenAI's Realtime API
with WebSocket connections for low-latency transcription.
""" 