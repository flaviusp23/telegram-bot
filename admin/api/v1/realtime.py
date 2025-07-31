"""
Real-time updates via Server-Sent Events (SSE)
"""
from datetime import datetime
from typing import AsyncGenerator
import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from admin.core.permissions import require_viewer, AdminUser
from database.database import get_db
from database.models import User, Response

router = APIRouter(tags=["realtime"])

# Store active connections
active_connections = set()

async def event_generator(db: Session) -> AsyncGenerator[str, None]:
    """Generate SSE events with dashboard updates"""
    while True:
        try:
            # Get current stats
            total_patients = db.query(func.count(User.id)).scalar()
            active_patients = db.query(func.count(func.distinct(User.id))).filter(
                User.last_interaction.isnot(None)
            ).scalar()
            total_responses = db.query(func.count(Response.id)).scalar()
            
            # Create event data
            data = {
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "total_patients": total_patients,
                    "active_patients": active_patients,
                    "total_responses": total_responses
                }
            }
            
            # Send as SSE event
            yield f"data: {json.dumps(data)}\n\n"
            
            # Wait 5 seconds before next update
            await asyncio.sleep(5)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(5)

@router.get("/dashboard-updates")
async def dashboard_updates(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer)
):
    """
    Stream real-time dashboard updates via Server-Sent Events
    """
    return StreamingResponse(
        event_generator(db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )