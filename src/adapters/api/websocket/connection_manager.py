"""WebSocket connection manager for interview sessions."""

import logging
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for interviews."""

    def __init__(self):
        # interview_id → websocket
        self.active_connections: dict[UUID, WebSocket] = {}

    async def connect(self, interview_id: UUID, websocket: WebSocket):
        """Accept and register WebSocket connection.

        Args:
            interview_id: Interview UUID
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections[interview_id] = websocket
        logger.info(f"WebSocket connected for interview {interview_id}")

    def disconnect(self, interview_id: UUID):
        """Remove connection.

        Args:
            interview_id: Interview UUID
        """
        if interview_id in self.active_connections:
            del self.active_connections[interview_id]
            logger.info(f"WebSocket disconnected for interview {interview_id}")

    async def send_message(self, interview_id: UUID, message: dict):
        """Send message to specific interview connection.

        Args:
            interview_id: Interview UUID
            message: Message dictionary to send
        """
        websocket = self.active_connections.get(interview_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Send message to all connections.

        Args:
            message: Message dictionary to broadcast
        """
        for websocket in self.active_connections.values():
            await websocket.send_json(message)


# Global instance
manager = ConnectionManager()
