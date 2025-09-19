from __future__ import annotations

import time
from typing import Optional, Dict, Any

from contextlib import suppress

import asyncio
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig

from application.core.logging import get_logger
from external.clients.transcribe import AWSTranscribeRealtimeSTTClient
from application.utils.agents import exception, is_least_percentage_of_chunk_size
from application.services.vRecognition.state import State

logger = get_logger(__name__)

MIN_TRANSCRIPT_PERCENT: float = 0.20


class Transcriber:
    """Maintains per-connection STT state and emits transcript/actors to the graph.

    Responsibilities:
    - Buffer incoming base64 audio chunks and run a single realtime STT stream.
    - Accumulate partial and final transcripts; expose a normalised transcript string.
    - Track detected actors (from frames) and signal readiness to the graph when appropriate.
    - Manage the compiled graph invocation task lifecycle for the session.
    """

    def __init__(self, connection_id: str, timeout: int) -> None:
        self.connection_id: str = connection_id
        self.timeout: int = timeout

        self.actors: list[str] = []
        self.final_utterances: list[str] = []
        self.current_partial: Optional[str] = ""

        self._audio_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._stt_task: Optional[asyncio.Task] = None

        # Internal readiness events
        self._event_text_ready: asyncio.Event = asyncio.Event()
        self._event_actors_updated: asyncio.Event = asyncio.Event()
        self._has_minimum_transcript: bool = False

        # Graph management
        self.graph: Optional[CompiledStateGraph] = None
        self.graph_config: Optional[RunnableConfig] = None
        self.invoke_task: Optional[asyncio.Task] = None
        self.session_started: bool = False

    @property
    def transcript_text(self) -> str:
        parts = self.final_utterances[:]
        if self.current_partial:
            parts.append(self.current_partial)
        return " ".join(parts).strip().lower()

    async def enqueue_audio_chunk(self, audio_b64: str) -> None:
        """Enqueue a single base64-encoded PCM16 audio chunk for STT processing."""
        await self._audio_queue.put(audio_b64)

    def merge_actors(self, names: list[str]) -> None:
        """Merge new actor names into the set and signal if queryable.

        The graph should only proceed down actor-dependent paths after we have
        a minimum viable transcript, so we gate the event accordingly.
        """
        updated: bool = False
        existing = set(self.actors)
        for name in names:
            if name not in existing:
                self.actors.append(name)
                existing.add(name)
                updated = True
        if updated and self._has_minimum_transcript:
            self._event_actors_updated.set()

    async def _iter_audio_chunks(self):
        while True:
            chunk = await self._audio_queue.get()
            if chunk is None:
                break
            yield chunk

    async def _handle_transcript_event(self, event: Dict[str, Any]) -> None:
        text = (event.get("text") or "").strip()
        if not text:
            return

        is_partial = bool(event.get("is_partial", False))

        if is_partial:
            self.current_partial = text
            return

        # Finalized
        self.final_utterances.append(text)
        self.current_partial = None

        # First time we have enough text → allow actors path and retriever
        if not self._has_minimum_transcript:
            if is_least_percentage_of_chunk_size(self.transcript_text, MIN_TRANSCRIPT_PERCENT):
                self._has_minimum_transcript = True
                self._event_text_ready.set()
        else:
            self._event_text_ready.set()

    def start_stt_stream(self, stt_client: AWSTranscribeRealtimeSTTClient) -> None:
        """Start the realtime STT stream if not already running."""
        if self._stt_task and not self._stt_task.done():
            return

        async def _run():
            try:
                await stt_client.transcribe(
                    self._iter_audio_chunks(),
                    on_transcript=self._handle_transcript_event,
                )
            except asyncio.CancelledError:
                # Normal during shutdown; allow graceful exit
                raise
            except Exception as e:
                logger.error(f"STT stream failed for session {self.connection_id}: {e}")

        self._stt_task = asyncio.create_task(_run())

    @exception
    async def run(self, state: State) -> Dict[str, Any]:
        """Wait until we have either enough transcript or an actor update, then emit state.

        Returns a partial state update containing the normalized transcript and
        the current list of actors. On timeout, returns an error and signals end.
        """
        start_time = float(state["start_time"]) if state["start_time"] else time.monotonic()
        time_remaining = max(0.0, self.timeout - (time.monotonic() - start_time))

        wait_text_ready = asyncio.create_task(self._event_text_ready.wait())
        wait_actors_updated = asyncio.create_task(self._event_actors_updated.wait())
        done, pending = await asyncio.wait(
            {wait_text_ready, wait_actors_updated},
            timeout=time_remaining,
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Clean-up pending waits
        for task in pending:
            task.cancel()

        if not done:
            return {
                "error": {
                    "type": "systemError",
                    "message": f"Timeout after {self.timeout} seconds",
                    "node": self.__class__.__name__,
                },
                "end": True,
            }

        self._event_text_ready.clear()
        self._event_actors_updated.clear()

        return {"transcript": self.transcript_text, "actors": self.actors}

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

    async def shutdown(self) -> None:
        try:
            try:
                await self._flush_queue()
            except asyncio.CancelledError:
                pass
            await self._audio_queue.put(None)
            await self._wait_or_cancel(self._stt_task)
        finally:
            pass
