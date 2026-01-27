from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """Manager for WebSocket connections."""
    
    def __init__(self):
        # Store active connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store user metadata
        self.user_metadata: Dict[str, Dict[str, Any]] = {}
        # Background task for ping/pong
        self.background_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new client."""
        try:
            await websocket.accept()
            
            if client_id not in self.active_connections:
                self.active_connections[client_id] = []
            
            self.active_connections[client_id].append(websocket)
            
            # Store connection metadata
            self.user_metadata[client_id] = {
                "connected_at": datetime.utcnow().isoformat(),
                "last_ping": datetime.utcnow().isoformat(),
                "messages_sent": 0,
                "messages_received": 0
            }
            
            logger.info(f"Client {client_id} connected")
            
            # Start background ping task if not running
            if not self.background_task or self.background_task.done():
                self.background_task = asyncio.create_task(self._ping_clients())
                
        except Exception as e:
            logger.error(f"Failed to connect client {client_id}: {str(e)}")
            raise

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """Disconnect a client."""
        try:
            if client_id in self.active_connections:
                self.active_connections[client_id].remove(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
                    del self.user_metadata[client_id]
            
            logger.info(f"Client {client_id} disconnected")
            
        except Exception as e:
            logger.error(f"Failed to disconnect client {client_id}: {str(e)}")
            raise

    async def send_personal_message(self, message: Any, client_id: str):
        """Send a message to a specific client."""
        if client_id not in self.active_connections:
            logger.warning(f"Client {client_id} not found")
            return
        
        try:
            message_data = self._prepare_message(message)
            
            for connection in self.active_connections[client_id]:
                await connection.send_json(message_data)
            
            # Update metadata
            self.user_metadata[client_id]["messages_received"] += 1
            
            logger.debug(f"Sent message to client {client_id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {str(e)}")
            raise

    async def broadcast(self, message: Any, exclude: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        try:
            message_data = self._prepare_message(message)
            
            for client_id, connections in self.active_connections.items():
                if client_id != exclude:
                    for connection in connections:
                        await connection.send_json(message_data)
                        self.user_metadata[client_id]["messages_received"] += 1
            
            logger.debug(f"Broadcast message to {len(self.active_connections)} clients")
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {str(e)}")
            raise

    def _prepare_message(self, message: Any) -> dict:
        """Prepare message for sending."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "data": message
        }

    async def _ping_clients(self):
        """Background task to ping clients and remove dead connections."""
        while True:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                
                for client_id in list(self.active_connections.keys()):
                    for connection in self.active_connections[client_id][:]:
                        try:
                            await connection.send_json({"type": "ping"})
                            self.user_metadata[client_id]["last_ping"] = datetime.utcnow().isoformat()
                        except WebSocketDisconnect:
                            await self.disconnect(connection, client_id)
                        except Exception as e:
                            logger.error(f"Error pinging client {client_id}: {str(e)}")
                            await self.disconnect(connection, client_id)
                
            except Exception as e:
                logger.error(f"Error in ping task: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    def get_active_connections(self) -> Dict[str, int]:
        """Get count of active connections per client."""
        return {
            client_id: len(connections)
            for client_id, connections in self.active_connections.items()
        }

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_clients": len(self.active_connections),
            "total_connections": sum(len(conns) for conns in self.active_connections.values()),
            "clients": self.user_metadata
        }

# Global connection manager instance
manager = ConnectionManager()
