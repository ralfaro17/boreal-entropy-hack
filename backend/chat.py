import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections partitioned by chat room,

    broadcasting messages, maintaining recent history, and handling connection lifecycles.
    """

    def __init__(self, max_history: int = 100):
        # room_id -> {WebSocket: sender_name}
        self.active_connections: dict[str, dict[WebSocket, str]] = {}
        # room_id -> list[dict]
        self.history: dict[str, list[dict[str, Any]]] = {}
        self.max_history = max_history

    def format_message(
        self,
        room_id: str,
        sender_name: str,
        text: str,
        msg_type: str = "message",
    ) -> dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "room_id": room_id,
            "sender_name": sender_name,
            "text": text,
            "type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def connect(
        self,
        websocket: WebSocket,
        room_id: str,
        sender_name: str,
        initial_history: list[dict[str, Any]] | None = None,
    ):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][websocket] = sender_name

        if room_id not in self.history and initial_history:
            # Filter strictly to dialogue messages, excluding any transient presence events
            self.history[room_id] = [
                m for m in initial_history if m.get("type", "message") == "message"
            ]

        # Send existing message history to the newly connected participant
        history_msgs = self.get_history(room_id)
        if history_msgs:
            await websocket.send_json({
                "type": "history",
                "room_id": room_id,
                "messages": history_msgs,
            })

        # Broadcast transient join notification live to the room without saving to persistent history
        system_msg = self.format_message(
            room_id=room_id,
            sender_name="System",
            text=f"{sender_name} joined the chat",
            msg_type="system",
        )
        await self.broadcast(room_id, system_msg, save_to_history=False)

    async def disconnect(self, websocket: WebSocket, room_id: str):
        sender_name = "User"
        if room_id in self.active_connections:
            sender_name = self.active_connections[room_id].pop(websocket, "User")
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

        # Broadcast transient leave notification without saving to persistent history
        system_msg = self.format_message(
            room_id=room_id,
            sender_name="System",
            text=f"{sender_name} left the chat",
            msg_type="system",
        )
        await self.broadcast(room_id, system_msg, save_to_history=False)

    async def broadcast(self, room_id: str, message: dict[str, Any], save_to_history: bool = True):
        # ONLY save genuine dialogue messages to conversation history.
        # Transient presence events (joins, leaves, typing) are broadcast live to connected sockets
        # but NEVER persisted in conversation history, preventing LLM token pollution and DB bloat.
        if save_to_history and message.get("type") == "message":
            if room_id not in self.history:
                self.history[room_id] = []
            self.history[room_id].append(message)
            if len(self.history[room_id]) > self.max_history:
                self.history[room_id] = self.history[room_id][-self.max_history:]

        # Broadcast to all live WebSockets in the room
        connections = list(self.active_connections.get(room_id, {}).keys())
        stale_connections = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                stale_connections.append(connection)

        # Cleanup any broken connections
        for stale in stale_connections:
            if room_id in self.active_connections:
                self.active_connections[room_id].pop(stale, None)

    def get_active_rooms(self) -> list[dict[str, Any]]:
        rooms = []
        for room_id, conns in self.active_connections.items():
            rooms.append({
                "room_id": room_id,
                "active_users": len(conns),
                "users": list(conns.values()),
                "message_count": len(self.history.get(room_id, [])),
            })
        return rooms

    def get_history(self, room_id: str) -> list[dict[str, Any]]:
        return list(self.history.get(room_id, []))


# Singleton instance for the application
chat_manager = ConnectionManager()

