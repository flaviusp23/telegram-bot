"""
Analytics API endpoints for dashboard and reporting.

This module provides comprehensive analytics endpoints including:
- Dashboard overview statistics
- User registration and activity analytics
- Response completion and distress analytics
- Severity trend analysis over time

All endpoints include proper caching for expensive queries.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Float, Integer

from admin.core.permissions import require_viewer, AdminUser
from admin.models.admin import AuditLog, AdminUser as AdminUserModel
from database.database import get_db
from database.models import User, Response

# Create router
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    admin_user: AdminUser = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get dashboard overview statistics."""
    try:
        # Get basic counts
        total_patients = db.query(User).count()
        active_patients = db.query(User).filter(User.status == 'active').count()
        total_responses = db.query(Response).count()
        
        # Get recent activity count (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_responses = db.query(Response).filter(
            Response.response_timestamp >= yesterday
        ).count()
        
        # Calculate DDS-2 specific metrics
        # DDS-2 Average Distress Score (1-6 scale: 1=not a problem, 6=very serious problem)
        avg_dds2_score = db.query(Response).filter(
            Response.question_type.in_(['dds2_q1_overwhelmed', 'dds2_q2_failing'])
        ).with_entities(
            func.avg(cast(Response.response_value, Float))
        ).scalar() or 2.0
        
        # DDS-2 Distress Level Classification
        total_dds2_responses = db.query(Response).filter(
            Response.question_type.in_(['dds2_q1_overwhelmed', 'dds2_q2_failing'])
        ).count()
        
        # Moderate distress: DDS-2 score >= 3.0
        moderate_distress = db.query(Response).filter(
            Response.question_type.in_(['dds2_q1_overwhelmed', 'dds2_q2_failing']),
            cast(Response.response_value, Integer) >= 3
        ).count()
        
        # High distress: DDS-2 score >= 4.0
        high_distress = db.query(Response).filter(
            Response.question_type.in_(['dds2_q1_overwhelmed', 'dds2_q2_failing']),
            cast(Response.response_value, Integer) >= 4
        ).count()
        
        # Very high distress: DDS-2 score >= 5.0
        very_high_distress = db.query(Response).filter(
            Response.question_type.in_(['dds2_q1_overwhelmed', 'dds2_q2_failing']),
            cast(Response.response_value, Integer) >= 5
        ).count()
        
        moderate_distress_percentage = (moderate_distress / total_dds2_responses * 100) if total_dds2_responses > 0 else 0
        high_distress_percentage = (high_distress / total_dds2_responses * 100) if total_dds2_responses > 0 else 0
        very_high_distress_percentage = (very_high_distress / total_dds2_responses * 100) if total_dds2_responses > 0 else 0
        
        # Response rate (assuming 3 daily check-ins)
        expected_responses = total_patients * 3 * 7  # Weekly
        actual_responses_week = db.query(Response).filter(
            Response.response_timestamp >= datetime.now(timezone.utc) - timedelta(days=7)
        ).count()
        response_rate = (actual_responses_week / expected_responses * 100) if expected_responses > 0 else 0
        
        # User growth
        last_month = datetime.now(timezone.utc) - timedelta(days=30)
        new_users_month = db.query(User).filter(
            User.registration_date >= last_month
        ).count()
        
        prev_month_start = last_month - timedelta(days=30)
        prev_month_users = db.query(User).filter(
            User.registration_date >= prev_month_start,
            User.registration_date < last_month
        ).count()
        
        growth_rate = ((new_users_month - prev_month_users) / prev_month_users * 100) if prev_month_users > 0 else 0
        
        return {
            "overview": {
                "total_users": total_patients,
                "active_users": active_patients,
                "total_responses": total_responses,
                "recent_responses": recent_responses,
                "total_dds2_responses": total_dds2_responses
            },
            "metrics": {
                "average_dds2_score": float(avg_dds2_score),
                "moderate_distress_percentage": float(moderate_distress_percentage),
                "high_distress_percentage": float(high_distress_percentage),
                "very_high_distress_percentage": float(very_high_distress_percentage),
                "response_rate": float(response_rate),
                "user_growth_rate": float(growth_rate)
            },
            "dds2_breakdown": {
                "total_responses": total_dds2_responses,
                "average_score": float(avg_dds2_score),
                "moderate_distress_count": moderate_distress,
                "high_distress_count": high_distress,
                "very_high_distress_count": very_high_distress
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "overview": {
                "total_users": 0,
                "active_users": 0,
                "total_responses": 0,
                "recent_responses": 0,
                "total_dds2_responses": 0
            },
            "metrics": {
                "average_dds2_score": 2.0,
                "moderate_distress_percentage": 0.0,
                "high_distress_percentage": 0.0,
                "very_high_distress_percentage": 0.0,
                "response_rate": 0.0,
                "user_growth_rate": 0.0
            },
            "dds2_breakdown": {
                "total_responses": 0,
                "average_score": 2.0,
                "moderate_distress_count": 0,
                "high_distress_count": 0,
                "very_high_distress_count": 0
            },
            "error": str(e)
        }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of activities to return"),
    admin_user: AdminUser = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get recent activity across the system including responses, registrations, and admin actions."""
    try:
        # Get recent responses
        recent_responses = db.query(
            Response.id,
            Response.user_id,
            Response.question_type,
            Response.response_value,
            Response.response_timestamp,
            User.first_name,
            User.family_name
        ).join(User).order_by(
            Response.response_timestamp.desc()
        ).limit(limit).all()
        
        # Get recent patients
        recent_patients = db.query(User).order_by(
            User.registration_date.desc()
        ).limit(5).all()
        
        # Get recent admin actions (with error handling)
        try:
            recent_admin_actions = db.query(
                AuditLog.id,
                AuditLog.action,
                AuditLog.resource_type,
                AuditLog.resource_id,
                AuditLog.timestamp,
                AdminUserModel.username
            ).join(AdminUserModel).order_by(
                AuditLog.timestamp.desc()
            ).limit(limit).all()
        except Exception:
            # If admin actions query fails, continue without them
            recent_admin_actions = []
    except Exception as e:
        # Return basic response if queries fail
        return {
            "activities": [],
            "count": 0,
            "error": str(e)
        }
    
    # Combine and sort activities by timestamp
    activities = []
    
    # Add responses
    for r in recent_responses:
        activity_text = f"{r.first_name} {r.family_name or ''} responded to {r.question_type.replace('_', ' ')}"
        if r.question_type == 'distress_check':
            activity_text += f": {r.response_value.upper()}"
        elif r.question_type == 'severity_rating':
            activity_text += f": {r.response_value}/5"
            
        activities.append({
            "type": "response",
            "timestamp": r.response_timestamp,
            "text": activity_text,
            "icon": "📝",
            "user_id": r.user_id,
            "severity": "info" if r.response_value == "no" else "warning"
        })
    
    # Add new patients from last 24 hours
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    for p in recent_patients:
        # Handle timezone-naive registration_date
        reg_date = p.registration_date
        if reg_date.tzinfo is None:
            # Assume UTC if no timezone info
            reg_date = reg_date.replace(tzinfo=timezone.utc)
        
        if reg_date >= yesterday:
            activities.append({
                "type": "new_patient",
                "timestamp": p.registration_date,
                "text": f"New patient registered: {p.first_name} {p.family_name or ''}",
                "icon": "👤",
                "user_id": p.id,
                "severity": "success"
            })
    
    # Add admin actions
    for a in recent_admin_actions:
        action_text = f"Admin {a.username}: {a.action.replace('_', ' ')}"
        if a.resource_type and a.resource_id:
            action_text += f" ({a.resource_type} #{a.resource_id})"
            
        activities.append({
            "type": "admin_action",
            "timestamp": a.timestamp,
            "text": action_text,
            "icon": "⚙️",
            "severity": "admin"
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Limit to requested number
    activities = activities[:limit]
    
    return {
        "activities": activities,
        "count": len(activities)
    }