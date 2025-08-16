import time
from typing import Optional, Dict, Any

from contextlib import suppress

import asyncio
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig

from application.core.logging import get_logger
from external.clients.transcribe import AWSTranscribeRealtimeSTTClient
from application.services.vRecognition.utils import exception, is_least_percentage_of_chunk_size
from application.services.vRecognition.state import State

logger = get_logger(__name__)


class Transcriber:
    def __init__(self, connection_id: str, timeout: int):
        self.connection_id = connection_id
        self.timeout = timeout

        self.actors: list[str] = []
        self.final_utterances: list[str] = []
        self.current_partial: Optional[str] = ""

        self._audio_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._stt_task: Optional[asyncio.Task] = None

        self._evt_text: asyncio.Event = asyncio.Event()
        self._evt_actor: asyncio.Event = asyncio.Event()
        self._transcript_checked: bool = False

        # Graph management
        self.graph: CompiledStateGraph = None
        self.graph_config: RunnableConfig = None
        self.invoke_task: Optional[asyncio.Task] = None
        self.session_started: bool = False

    @property
    def transcript_text(self) -> str:
        parts = self.final_utterances[:]
        if self.current_partial:
            parts.append(self.current_partial)
        return " ".join(parts).strip().lower()

    async def push_audio_chunk(self, audio_b64: str) -> None:
        await self._audio_queue.put(audio_b64)

    def update_actors(self, names: list[str]) -> None:
        updated = False
        existing = set(self.actors)
        for name in names:
            if name not in existing:
                self.actors.append(name)
                existing.add(name)
                updated = True
        if updated and self._transcript_checked:
            # can't query actors until we have enough text
            self._evt_actor.set()

    async def _audio_generator(self):
        while True:
            chunk = await self._audio_queue.get()
            if chunk is None:
                break
            yield chunk

    async def _on_transcript(self, event: Dict[str, Any]):
        text = (event.get("text") or "").strip()
        if not text:
            return

        is_partial = bool(event.get("is_partial", False))

        if is_partial:
            self.current_partial = text
        else:
            self.final_utterances.append(text)
            self.current_partial = None

            if not self._transcript_checked:
                if is_least_percentage_of_chunk_size(self.transcript_text, 0.3):
                    self._transcript_checked = True
            else:
                self._evt_text.set()

    def ensure_stt_stream(self, stt_client: AWSTranscribeRealtimeSTTClient) -> None:
        if self._stt_task and not self._stt_task.done():
            return

        async def _run():
            try:
                await stt_client.transcribe(
                    self._audio_generator(),
                    on_transcript=self._on_transcript,
                )
            except Exception as e:
                logger.error(f"STT stream failed for session {self.connection_id}: {e}")

        self._stt_task = asyncio.create_task(_run())

    @exception
    async def run(self, state: State):
        start_time = float(state["start_time"]) if state["start_time"] else time.monotonic()
        time_remaining = max(0.0, self.timeout - (time.monotonic() - start_time))
        wait_text = asyncio.create_task(self._evt_text.wait())
        wait_actor = asyncio.create_task(self._evt_actor.wait())
        done, pending = await asyncio.wait(
            {wait_text, wait_actor},
            timeout=time_remaining,
            return_when=asyncio.FIRST_COMPLETED
        )
        # Clean-up pending waits
        for t in pending:
            t.cancel()

        if not done:
            return {
                "error": {
                    "type": "timeout",
                    "message": f"Timeout after {self.timeout} seconds",
                    "node": self.__class__.__name__,
                }
            }

        self._evt_text.clear()
        self._evt_actor.clear()

        return {
            "transcript": self.transcript_text,
            "actors": self.actors
        }

    async def _flush_queue(self, timeout: float = 3.0) -> None:
        """Wait until the audio queue is empty (best-effort, bounded by timeout)."""
        deadline = asyncio.get_event_loop().time() + timeout
        while not self._audio_queue.empty() and asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(0.01)

    @staticmethod
    async def _wait_or_cancel(task: Optional[asyncio.Task], timeout: float = 5.0) -> None:
        """Wait for task to finish; cancel if it exceeds timeout."""
        if not task:
            return
        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        except asyncio.CancelledError:
            pass

    async def close(self) -> None:
        try:
            try:
                await self._flush_queue()
            except asyncio.CancelledError:
                pass
            await self._audio_queue.put(None)
            await self._wait_or_cancel(self._stt_task)
        finally:
            pass
