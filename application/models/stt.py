from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class STTMessageType(str, Enum):
    """Types of STT messages from OpenAI Realtime API."""
    TRANSCRIPTION           = "input_audio_buffer.transcription"
    TRANSCRIPTION_PARTIAL   = "input_audio_buffer.transcription_partial"
    SPEECH_STOPPED          = "input_audio_buffer.speech_stopped"
    CONVERSATION_CREATED    = "conversation.item.created"

class STTResult(BaseModel):
    """Result from OpenAI Realtime STT."""
    text:       str
    is_final:   bool = True
    is_partial: bool = False
    language:   Optional[str] = None
    confidence: Optional[float] = None
    timestamp:  datetime = Field(default_factory=datetime.utcnow)
    message_type: Optional[STTMessageType] = None
    metadata:   Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_openai_message(cls, message: Dict[str, Any]) -> "STTResult":
        """Create STTResult from OpenAI Realtime API message."""
        message_type = message.get("type")
        
        if message_type == STTMessageType.TRANSCRIPTION:
            return cls(
                text=message.get("text", ""),
                is_final=True,
                is_partial=False,
                language=message.get("language"),
                confidence=message.get("confidence"),
                message_type=STTMessageType.TRANSCRIPTION,
                metadata=message
            )
        elif message_type == STTMessageType.TRANSCRIPTION_PARTIAL:
            return cls(
                text=message.get("text", ""),
                is_final=False,
                is_partial=True,
                language=message.get("language"),
                confidence=message.get("confidence"),
                message_type=STTMessageType.TRANSCRIPTION_PARTIAL,
                metadata=message
            )
        else:
            # Handle other message types
            return cls(
                text="",
                is_final=False,
                is_partial=False,
                message_type=STTMessageType(message_type) if message_type else None,
                metadata=message
            )
