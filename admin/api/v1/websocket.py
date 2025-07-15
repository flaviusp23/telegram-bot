"""
WebSocket support for real-time updates
"""
from typing import Dict, Set
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import jwt
from jwt import PyJWTError

from database.database import get_db
from database.models import User, Response, AssistantInteraction
from admin.core.config import settings
from admin.models.admin import AdminUser

router = APIRouter(tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "users": set(),
            "logs": set()
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
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    await manager.connect(websocket, "dashboard")
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        # Start sending periodic updates
        while True:
            # Get latest stats
            stats = {
                "type": "stats_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "total_users": db.query(func.count(User.id)).scalar(),
                    "active_users": db.query(func.count(func.distinct(AssistantInteraction.user_id))).scalar(),
                    "total_responses": db.query(func.count(Response.id)).scalar(),
                    "recent_activity": []  # Add recent activity here
                }
            }
            
            await websocket.send_json(stats)
            
            # Wait for 5 seconds or until client sends a message
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                # Handle client messages if needed
                if message == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
        manager.disconnect(websocket, "dashboard")