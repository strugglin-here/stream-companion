"""WebSocket endpoint for real-time overlay updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.websocket import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_type: str = Query("overlay", description="Client type: 'overlay' or 'control'")
):
    """
    WebSocket endpoint for real-time updates.
    
    **Connection URL**: `ws://localhost:8002/ws?client_type=overlay`
    
    **Client Types**:
    - `overlay`: Browser source overlays (receive element updates)
    - `control`: Control panel clients (receive status updates)
    
    **Message Format** (Server → Client):
    ```json
    {
        "type": "element_update",
        "action": "show|hide|update|delete",
        "element": {...}
    }
    ```
    
    **Example Messages**:
    - Element animation start:
      ```json
      {
          "type": "element_update",
          "action": "show",
          "element": {"id": 1, "name": "confetti", "playing": true, "behavior": [...]}
      }
      ```
    
    - Element deleted:
      ```json
      {
          "type": "element_update",
          "action": "delete",
          "element_id": 1
      }
      ```
    
    - Connection confirmed:
      ```json
      {
          "type": "connection",
          "status": "connected",
          "client_type": "overlay"
      }
      ```
    """
    # Validate client type
    if client_type not in ["overlay", "control"]:
        await websocket.close(code=1003, reason="Invalid client_type. Use 'overlay' or 'control'")
        return
    
    # Connect the client
    await manager.connect(websocket, group=client_type)
    
    # Send connection confirmation
    await manager.send_personal_message(
        {
            "type": "connection",
            "status": "connected",
            "client_type": client_type,
            "message": f"Connected to Stream Companion as {client_type}"
        },
        websocket
    )
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Handle ping/pong for keepalive
            if data.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong"},
                    websocket
                )
                continue
            
            # Log other messages (for debugging/future features)
            logger.info(f"Received message from {client_type}: {data}")
            
            # Echo message back for testing
            await manager.send_personal_message(
                {
                    "type": "echo",
                    "original": data
                },
                websocket
            )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, group=client_type)
        logger.info(f"{client_type} client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, group=client_type)
