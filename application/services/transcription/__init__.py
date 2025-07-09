from .stt import STTService

# Create singleton instance
stt_service = STTService()

__all__ = [
    "stt_service",
    "STTService"
]

"""
STT (Speech-to-Text) service module for real-time transcription.
This module provides real-time speech-to-text capabilities using OpenAI's Realtime API
with WebSocket connections for low-latency transcription.
""" 