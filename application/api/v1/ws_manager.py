import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Optional, Set, Iterable

from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from loguru import logger


class ConnectionManager:
    """
    Manages WebSocket connections and their lifecycle safely.

    Key guarantees:
    - All public methods are defensive: callers need no pre-checks.
    - Per-connection operations are serialized to avoid race conditions.
    - Sends fail-safe: any error triggers clean-up, no exceptions leak out.
    - Tasks tied to a connection are tracked and cancelled on close.
    """

    def __init__(self) -> None:
        self._conns: Dict[str, WebSocket] = {}
        self._conn_locks: Dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()
        self._tasks: Dict[str, Set[asyncio.Task]] = {}

    def __contains__(self, connection_id: str) -> bool:
        return connection_id in self._conns

    def __len__(self) -> int:
        return len(self._conns)

    def get_active_connection_count(self) -> int:
        return len(self._conns)

    def get_connection(self, connection_id: str) -> Optional[WebSocket]:
        return self._conns.get(connection_id)

    def active_ids(self) -> Iterable[str]:
        return tuple(self._conns.keys())

    def is_connected(self, connection_id: str) -> bool:
        ws = self._conns.get(connection_id)
        if not ws:
            return False
        # Check both client and application sides are still CONNECTED
        return (
            ws.client_state == WebSocketState.CONNECTED and
            ws.application_state == WebSocketState.CONNECTED
        )

    def _get_lock(self, connection_id: str) -> asyncio.Lock:
        return self._conn_locks.setdefault(connection_id, asyncio.Lock())

    async def connect(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        """Accept a new WebSocket (if not already accepted), register it, and return its id."""
        try:
            # Accept only if still CONNECTING
            if websocket.client_state == WebSocketState.CONNECTING:
                await websocket.accept()
        except Exception as e:
            logger.exception(f"Failed to accept WebSocket: {e}")
            await websocket.close()

        cid = connection_id or str(uuid.uuid4())

        async with self._registry_lock:
            self._conns[cid] = websocket
            self._conn_locks.setdefault(cid, asyncio.Lock())
            self._tasks.setdefault(cid, set())

        logger.info(f"WebSocket connected: {cid}")
        return cid

    def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket from registry without attempting to close it.
        Internal use; prefer close_connection() for graceful shutdown."""
        if connection_id in self._conns:
            self._conns.pop(connection_id, None)
            self._conn_locks.pop(connection_id, None)
            # Cancel any leftover done callbacks/empty sets
            for t in self._tasks.pop(connection_id, set()):
                # Task should have been cancelled already; ensure clean-up
                t.cancel()
            logger.info(f"WebSocket disconnected: {connection_id}")

    async def close_connection(self, connection_id: str, code: int = 1000, reason: str = "") -> None:
        """Gracefully close a WebSocket and clean up all trackings.
        Cancels any tracked tasks for this connection."""
        ws = self._conns.get(connection_id)
        if not ws:
            # Already gone—nothing to do
            self.disconnect(connection_id)
            return

        lock = self._get_lock(connection_id)
        async with lock:
            # Cancel associated tasks first to prevent late sends
            await self.cancel_tasks(connection_id, wait=False)

            try:
                if self.is_connected(connection_id):
                    await ws.close(code=code)
                    logger.info(f"WebSocket connection closed: {connection_id} (code={code}, reason='{reason}')")
            except Exception as e:
                logger.error(f"Error closing WebSocket {connection_id}: {e}")
            finally:
                self.disconnect(connection_id)

    @asynccontextmanager
    async def session(self, websocket: WebSocket, connection_id: Optional[str] = None):
        """Async context manager to auto-register and clean up a WebSocket.
        Usage:
            async with manager.session(websocket) as cid:
                ... # handle messages
        """
        cid = await self.connect(websocket, connection_id)
        try:
            yield cid
        finally:
            await self.close_connection(cid)

    async def _send_json_safe(self, connection_id: str, payload: dict) -> bool:
        """Internal: serialize send it per-connection; auto-clean-up on failure.
        Returns True on success, False otherwise."""
        ws = self._conns.get(connection_id)
        if not ws:
            return False

        lock = self._get_lock(connection_id)
        async with lock:
            try:
                if not self.is_connected(connection_id):
                    # If not connected, ensure clean-up and fail fast
                    await self.close_connection(connection_id)
                    return False
                await ws.send_json(payload)
                return True
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                # Any send failure leads to clean-up to prevent zombie entries
                await self.close_connection(connection_id)
                return False

    async def send_msg(self, connection_id: str, message: dict) -> bool:
        """Send a JSON message to a specific connection. Returns success flag."""
        return await self._send_json_safe(connection_id, message)

    async def send_text(self, connection_id: str, text: str) -> bool:
        ws = self._conns.get(connection_id)
        if not ws:
            return False
        lock = self._get_lock(connection_id)
        async with lock:
            try:
                if not self.is_connected(connection_id):
                    await self.close_connection(connection_id)
                    return False
                await ws.send_text(text)
                return True
            except Exception as e:
                logger.error(f"Error sending text to {connection_id}: {e}")
                await self.close_connection(connection_id)
                return False

    async def send_err_msg(self, connection_id: str, message: str) -> None:
        """Send an error message to a specific connection and close it."""
        await self._send_json_safe(connection_id, {
            "type": "error",
            "message": message or "Unexpected error occurred",
        })
        await self.close_connection(connection_id)

    async def send_cancel_msg(self, connection_id: str, message: str) -> None:
        """Send a cancel message to a specific connection and close it."""
        await self._send_json_safe(connection_id, {
            "status": "canceled",
            "message": message or "Document generation canceled",
        })
        await self.close_connection(connection_id)

    async def broadcast(self, message: dict) -> None:
        """Send a message to all active connections; stale ones are cleaned up."""
        # Snapshot to avoid dict-size-changed errors
        targets = list(self._conns.keys())
        # Fire concurrently but handle each safely
        await asyncio.gather(
            *(self._send_json_safe(cid, message) for cid in targets),
            return_exceptions=True,
        )

    async def close_all(self, code: int = 1001, reason: str = "Server shutdown") -> None:
        """Gracefully close all sockets and cancel their tasks."""
        targets = list(self._conns.keys())
        await asyncio.gather(
            *(self.close_connection(cid, code=code, reason=reason) for cid in targets),
            return_exceptions=True,
        )

    def track_task(self, connection_id: str, task: asyncio.Task) -> None:
        """Register a task tied to this connection.
        It will be auto-removed on completion and cancelled on close."""
        if connection_id not in self._tasks:
            # If a task arrives for an unknown connection, cancel it immediately
            task.cancel()
            return

        self._tasks[connection_id].add(task)

        def _cleanup(_t: asyncio.Task) -> None:
            # Remove on completion, ignoring if registry already cleared
            tasks = self._tasks.get(connection_id)
            if tasks is not None:
                tasks.discard(_t)
            # Log task errors
            if _t.cancelled():
                logger.debug(f"Task for {connection_id} cancelled")
            else:
                exc = _t.exception()
                if exc:
                    logger.error(f"Task for {connection_id} errored: {exc}")

        task.add_done_callback(_cleanup)

    async def cancel_tasks(self, connection_id: str, wait: bool = False) -> None:
        """Cancel all tasks tracked for this connection.
        If wait=True, awaits their completion."""
        tasks = self._tasks.get(connection_id)
        if not tasks:
            return

        for t in list(tasks):
            if not t.done():
                t.cancel()

        if wait:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def run_singleton(
        self,
        connection_id: str,
        name: str,
        coro_factory,
    ) -> Optional[asyncio.Task]:
        """
        Ensure only one task with a given 'name' runs per connection.
        If an older one exists, it is cancelled first.
        'coro_factory' must be a callable returning a coroutine.
        """
        # Stash a dict of named tasks inside _tasks by using a hidden task set entry
        # Alternative simple strategy: cancel *all* tasks first, then schedule one
        await self.cancel_tasks(connection_id, wait=False)
        try:
            coro = coro_factory()
            task = asyncio.create_task(coro, name=f"{connection_id}:{name}")
            self.track_task(connection_id, task)
            return task
        except Exception as e:
            logger.error(f"Failed to start singleton task '{name}' for {connection_id}: {e}")
            return None
