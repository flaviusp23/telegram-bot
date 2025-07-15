"""
Data export endpoints for admin panel
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd
from io import BytesIO
from fastapi import APIRouter, Depends, Query, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.database import get_db
from database.models import User, Response
from admin.core.permissions import require_viewer, AdminUser, require_admin

router = APIRouter(tags=["export"])

@router.get("/responses")
async def export_responses(
    format: str = Query("csv", description="Export format: csv or excel"),
    days: int = Query(30, description="Number of days to export", ge=1, le=365),
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer)
):
    """
    Export response data in CSV or Excel format
    """
    # Calculate date range using UTC
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Query responses with user info
    query = db.query(
        Response.id,
        User.first_name,
        User.family_name,
        User.telegram_id,
        Response.question_type,
        Response.response_value,
        Response.response_timestamp
    ).join(User).filter(
        Response.response_timestamp >= start_date
    )
    
    # Filter by user if specified
    if user_id:
        query = query.filter(Response.user_id == user_id)
    
    query = query.order_by(Response.response_timestamp.desc())
    
    # Convert to DataFrame
    data = []
    for row in query.all():
        data.append({
            'Response ID': row.id,
            'First Name': row.first_name,
            'Last Name': row.family_name,
            'Telegram ID': row.telegram_id,
            'Question Type': row.question_type,
            'Response': row.response_value,
            'Timestamp': row.response_timestamp
        })
    
    df = pd.DataFrame(data)
    
    # Generate file
    if format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Responses', index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=responses_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
            }
        )
    else:  # CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=responses_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

@router.get("/users")
async def export_users(
    format: str = Query("csv", description="Export format: csv or excel"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_admin)
):
    """
    Export user data (requires admin role)
    """
    # Query all users
    users = db.query(User).all()
    
    # Convert to DataFrame
    data = []
    for user in users:
        data.append({
            'User ID': user.id,
            'First Name': user.first_name,
            'Last Name': user.family_name,
            'Telegram ID': user.telegram_id,
            'Email': user.email,
            'Phone': user.phone_number,
            'Status': user.status.value,
            'Registration Date': user.registration_date,
            'Last Interaction': user.last_interaction
        })
    
    df = pd.DataFrame(data)
    
    # Generate file
    if format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Users', index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=users_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
            }
        )
    else:  # CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=users_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )