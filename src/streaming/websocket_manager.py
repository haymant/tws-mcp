"""WebSocket connection manager for streaming subscriptions."""

from typing import Dict, List, Any
from starlette.websockets import WebSocket


class StreamingManager:
    """Manages WebSocket connections and TWS subscriptions."""
    
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {
            "market_data": [],
            "portfolio": [],
            "news": []
        }
        self.subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, stream_type: str):
        """Register a new WebSocket connection."""
        await websocket.accept()
        if stream_type in self.connections:
            self.connections[stream_type].append(websocket)
            self.subscriptions[websocket] = {"type": stream_type, "active": []}
    
    async def disconnect(self, websocket: WebSocket, stream_type: str):
        """Unregister a WebSocket connection and cleanup subscriptions."""
        if stream_type in self.connections and websocket in self.connections[stream_type]:
            self.connections[stream_type].remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
    
    async def broadcast(self, stream_type: str, message: dict):
        """Broadcast a message to all connected clients of a stream type."""
        disconnected = []
        for websocket in self.connections.get(stream_type, []):
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Cleanup disconnected clients
        for ws in disconnected:
            await self.disconnect(ws, stream_type)
