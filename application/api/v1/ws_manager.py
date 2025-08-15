import uuid
from typing import Dict

from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from loguru import logger


class ConnectionManager:
    """Manages WebSocket connections for the application."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str | None = None,
    ) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        cid = connection_id or str(uuid.uuid4())
        self.active_connections[cid] = websocket
        logger.info(f"WebSocket connected: {cid}")
        return cid

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")

    async def close_connection(self, connection_id: str):
        """Properly close a WebSocket connection by sending close the frame and cleaning up."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                if websocket.client_state != WebSocketState.CONNECTED:
                    self.disconnect(connection_id)
                    return
                await websocket.close()
                logger.info(f"WebSocket connection closed: {connection_id}")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection {connection_id}: {e}")
            finally:
                self.disconnect(connection_id)

    async def send_msg(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def send_err_msg(self, connection_id: str, message: str):
        """Send an error message to a specific connection and close it."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json({
                    "type": "error",
                    "message": message or "Unexpected error occurred"
                })
            except Exception as e:
                logger.error(f"Error sending error message to {connection_id}: {e}")
            finally:
                await self.close_connection(connection_id)

    async def send_cancel_msg(self, connection_id: str, message: str):
        """Send a cancel message to a specific connection and close it."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json({
                    "status": "canceled",
                    "message": message or "Document generation canceled"
                })
            except Exception as e:
                logger.error(f"Error sending cancel message to {connection_id}: {e}")
            finally:
                await self.close_connection(connection_id)

    async def broadcast(self, message: dict):
        """Send a message to all active connections."""
        disconnected_ids = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected_ids.append(connection_id)
        for connection_id in disconnected_ids:
            self.disconnect(connection_id)

    def get_connection(self, connection_id: str) -> WebSocket | None:
        """Get a specific WebSocket connection."""
        return self.active_connections.get(connection_id)

    def is_connected(self, connection_id: str) -> bool:
        """Check if a connection is active."""
        return connection_id in self.active_connections

    def get_active_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)