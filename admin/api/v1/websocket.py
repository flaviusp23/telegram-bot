"""
WebSocket support for real-time updates
"""
from datetime import datetime
from typing import Dict, Set
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from admin.constants import WebSocketSettings
from admin.core.config import settings
from admin.models.admin import AdminUser
from database.database import get_db
from database.models import User, Response, AssistantInteraction
from jwt import PyJWTError
import jwt

router = APIRouter(tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            channel: set() for channel in WebSocketSettings.CHANNELS
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self.active_connections[channel].add(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str):
        self.active_connections[channel].discard(websocket)
    
    async def broadcast_to_channel(self, message: dict, channel: str):
        """Send message to all connections in a channel"""
        if channel in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[channel].discard(conn)

manager = ConnectionManager()

async def get_current_user_from_token(token: str, db: Session) -> AdminUser:
    """Validate JWT token and return user"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        return user if user and user.is_active else None
    except PyJWTError:
        return None

@router.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time dashboard updates"""
    # Authenticate user
    user = await get_current_user_from_token(token, db)
    if not user:
        await websocket.close(code=WebSocketSettings.ERROR_UNAUTHORIZED, reason="Unauthorized")
        return
    
    await manager.connect(websocket, "dashboard")
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": WebSocketSettings.MSG_CONNECTED,
            "timestamp": datetime.now().isoformat()
        })
        
        # Start sending periodic updates
        while True:
            # Get latest stats
            stats = {
                "type": WebSocketSettings.MSG_STATS_UPDATE,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "total_patients": db.query(func.count(User.id)).scalar(),
                    "active_users": db.query(func.count(func.distinct(AssistantInteraction.user_id))).scalar(),
                    "total_responses": db.query(func.count(Response.id)).scalar(),
                    "recent_activity": []  # Add recent activity here
                }
            }
            
            await websocket.send_json(stats)
            
            # Wait for ping timeout or until client sends a message
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=WebSocketSettings.PING_TIMEOUT
                )
                # Handle client messages if needed
                if message == WebSocketSettings.MSG_PING:
                    await websocket.send_json({"type": WebSocketSettings.MSG_PONG})
            except asyncio.TimeoutError:
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
    except Exception as e:
        await websocket.close(code=WebSocketSettings.ERROR_GENERAL, reason=str(e))
        manager.disconnect(websocket, "dashboard")