import datetime
from typing import Dict, Any, Optional

import asyncio

from application.core.logging import get_logger
from external.clients.openai import OpenAIRealtimeSTTClient
#from application.core.dependencies import mongo_manager, stt_client

logger = get_logger(__name__)


class IdentificationPipeline:
    """Per-session real-time pipeline storing actors and transcript, with a live STT stream."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.actors: list[str] = []
        self.transcript_text: str = ""
        self.created_at = datetime.datetime.now().isoformat()
        self._audio_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._stt_task: Optional[asyncio.Task] = None
        self._closing: bool = False

    async def push_audio_chunk(self, audio_b64: str) -> None:
        await self._audio_queue.put(audio_b64)

    def update_actors(self, names: list[str]) -> None:
        if not names:
            return
        # todo, remove this debug print in production
        print(names)
        existing = set(self.actors)
        for name in names:
            if name not in existing:
                self.actors.append(name)
                existing.add(name)

    def append_transcript(self, text: str) -> None:
        if not text:
            return
        self.transcript_text += (" " if self.transcript_text else "") + text

    async def _audio_generator(self):
        while True:
            chunk = await self._audio_queue.get()
            if chunk is None:
                break
            yield chunk

    async def _on_transcript(self, event: Dict[str, Any]):
        text = event.get("text")
        if text:
            self.append_transcript(text)

    # TODO: Use self.actors and self.transcript_text to query Mongo and prepare identification results

    def ensure_stt_stream(self, stt_client: OpenAIRealtimeSTTClient) -> None:
        if self._stt_task and not self._stt_task.done():
            return

        async def _run():
            try:
                await stt_client.transcribe(
                    self._audio_generator(),
                    on_transcript=self._on_transcript,
                )
            except Exception as e:
                logger.error(f"STT stream failed for session {self.session_id}: {e}")

        self._stt_task = asyncio.create_task(_run())

    async def close(self):
        # Signal audio generator to finish and let STT send buffer end
        if not self._closing:
            self._closing = True
            try:
                await self._audio_queue.put(None)
            except Exception:
                pass

        # Wait briefly for STT task to finish gracefully
        if self._stt_task:
            try:
                await asyncio.wait_for(self._stt_task, timeout=2.0)
            except Exception:
                try:
                    self._stt_task.cancel()
                except Exception:
                    pass