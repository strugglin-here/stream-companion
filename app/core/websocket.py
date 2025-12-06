"""WebSocket connection manager for real-time overlay updates"""

from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Supports multiple connection groups (e.g., overlays vs control panels)
    for targeted message delivery.
    """
    
    def __init__(self):
        # Store active connections by group
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "overlay": set(),
            "control": set(),
        }
    
    async def connect(self, websocket: WebSocket, group: str = "overlay"):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to register
            group: Connection group (overlay, control, etc.)
        """
        await websocket.accept()
        
        if group not in self.active_connections:
            self.active_connections[group] = set()
        
        self.active_connections[group].add(websocket)
        logger.info(f"Client connected to '{group}' group. Total connections: {len(self.active_connections[group])}")
    
    def disconnect(self, websocket: WebSocket, group: str = "overlay"):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
            group: Connection group
        """
        if group in self.active_connections:
            self.active_connections[group].discard(websocket)
            logger.info(f"Client disconnected from '{group}' group. Remaining connections: {len(self.active_connections[group])}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific client.
        
        Args:
            message: Dictionary to send as JSON
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: dict, group: str = "overlay", exclude: WebSocket = None):
        """
        Broadcast a message to all connections in a group.
        
        Args:
            message: Dictionary to send as JSON
            group: Target connection group
            exclude: Optional WebSocket to exclude from broadcast
        """
        if group not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[group]:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, group)
    
    async def broadcast_to_all(self, message: dict):
        """
        Broadcast a message to all connected clients in all groups.
        
        Args:
            message: Dictionary to send as JSON
        """
        for group in self.active_connections.keys():
            await self.broadcast(message, group=group)
    
    def get_connection_count(self, group: str = None) -> int:
        """
        Get the number of active connections.
        
        Args:
            group: Optional group name. If None, returns total across all groups.
        
        Returns:
            Number of active connections
        """
        if group:
            return len(self.active_connections.get(group, set()))
        return sum(len(conns) for conns in self.active_connections.values())
    
    async def broadcast_element_update(self, element, action: str = "update"):
        """
        Broadcast an element update to overlay clients.
        
        Args:
            element: Element model instance
            action: Type of update (update, show, hide, delete)
        """
        message = {
            "type": "element_update",
            "action": action,
            "element": {
                "id": element.id,
                "widget_id": element.widget_id,
                "element_type": element.element_type.value if hasattr(element.element_type, 'value') else element.element_type,
                "name": element.name,
                "asset_path": element.asset_path,
                "properties": element.properties,
                "behavior": element.behavior,
                "visible": element.visible,
                "enabled": element.enabled
            }
        }
        await self.broadcast(message, group="overlay")
    
    async def broadcast_dashboard_event(self, event_type: str, dashboard_id: int):
        """
        Broadcast a dashboard event to overlay clients.
        
        Args:
            event_type: Event type (dashboard_activated, dashboard_deactivated)
            dashboard_id: Dashboard ID
        """
        message = {
            "type": event_type,
            "dashboard_id": dashboard_id
        }
        await self.broadcast(message, group="overlay")


# Global connection manager instance
manager = ConnectionManager()
