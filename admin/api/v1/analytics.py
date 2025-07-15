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
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, case, and_, extract, Integer
from sqlalchemy.orm import Session
from functools import lru_cache
import json
from collections import defaultdict

from database.database import get_db
from database.models import User, Response, AssistantInteraction, UserStatus
from admin.core.permissions import require_viewer, require_admin, AdminUser

router = APIRouter(tags=["analytics"])

# Cache configuration
CACHE_TTL_SECONDS = 30  # 30 seconds cache for analytics data (matches dashboard refresh)


class AnalyticsCache:
    """Simple in-memory cache for analytics data."""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            if datetime.now(timezone.utc) - self._timestamps[key] < timedelta(seconds=CACHE_TTL_SECONDS):
                return self._cache[key]
            else:
                # Remove expired cache
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cache value with current timestamp."""
        self._cache[key] = value
        self._timestamps[key] = datetime.now(timezone.utc)
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()


# Initialize cache instance
analytics_cache = AnalyticsCache()


@router.get("/dashboard")
async def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    fresh: bool = Query(False, description="Bypass cache and get fresh data")
) -> Dict[str, Any]:
    """
    Get dashboard overview statistics.
    
    Returns:
    - Total users (all time)
    - Active users (last 30 days)
    - Total responses
    - Average response rate
    - Recent distress percentage
    - User growth rate
    """
    # Permission already checked by dependency
    
    # Check cache (unless fresh data is requested)
    cache_key = f"dashboard_{days}"
    if not fresh:
        cached_data = analytics_cache.get(cache_key)
        if cached_data:
            return cached_data
    
    # Calculate date boundaries using UTC
    now = datetime.now(timezone.utc)
    days_ago = now - timedelta(days=days)
    
    # Total users
    total_users = db.query(func.count(User.id)).scalar()
    
    # Active users (users with last_interaction in the specified period)
    active_users = db.query(func.count(User.id)).filter(
        User.last_interaction >= days_ago
    ).scalar()
    
    # Total responses
    total_responses = db.query(func.count(Response.id)).scalar()
    
    # Responses in period
    responses_in_period = db.query(func.count(Response.id)).filter(
        Response.response_timestamp >= days_ago
    ).scalar()
    
    # Calculate distress percentage (responses with value 'yes' for distress_check)
    distress_count = db.query(func.count(Response.id)).filter(
        Response.response_timestamp >= days_ago,
        Response.question_type == 'distress_check',
        Response.response_value == 'yes'
    ).scalar()
    
    total_distress_checks = db.query(func.count(Response.id)).filter(
        Response.response_timestamp >= days_ago,
        Response.question_type == 'distress_check'
    ).scalar()
    
    distress_percentage = (distress_count / total_distress_checks * 100) if total_distress_checks > 0 else 0
    
    # User growth rate (compare current period with previous period)
    prev_period_start = days_ago - timedelta(days=days)
    
    users_current_period = db.query(func.count(User.id)).filter(
        User.registration_date >= days_ago
    ).scalar()
    
    users_prev_period = db.query(func.count(User.id)).filter(
        and_(
            User.registration_date >= prev_period_start,
            User.registration_date < days_ago
        )
    ).scalar()
    
    growth_rate = ((users_current_period - users_prev_period) / users_prev_period * 100) if users_prev_period > 0 else 0
    
    # Average severity rating for recent responses
    avg_severity = db.query(func.avg(func.cast(Response.response_value, Integer))).filter(
        Response.response_timestamp >= days_ago,
        Response.question_type == 'severity_rating'
    ).scalar() or 0
    
    # Response rate based on expected 3 questionnaires per day
    # Count actual responses in period
    total_responses_in_period = db.query(func.count(Response.id)).filter(
        Response.response_timestamp >= days_ago,
        Response.question_type == 'distress_check'  # Count distress checks as primary indicator
    ).scalar()
    
    # Calculate expected responses (3 per day * number of days * active users)
    expected_responses = 3 * days * active_users
    
    # Calculate engagement rate as percentage of expected responses
    response_rate = (total_responses_in_period / expected_responses * 100) if expected_responses > 0 else 0
    
    # Cap at 100% (in case of more responses than expected)
    response_rate = min(response_rate, 100.0)
    
    result = {
        "overview": {
            "total_users": total_users,
            "active_users": active_users,
            "total_responses": total_responses,
            "responses_in_period": responses_in_period
        },
        "metrics": {
            "distress_percentage": round(distress_percentage, 2),
            "average_severity": round(float(avg_severity), 2),
            "response_rate": round(response_rate, 2),
            "user_growth_rate": round(growth_rate, 2)
        },
        "period": {
            "days": days,
            "start_date": days_ago.isoformat(),
            "end_date": now.isoformat()
        }
    }
    
    # Cache the result
    analytics_cache.set(cache_key, result)
    
    return result


@router.get("/users/stats")
async def get_user_statistics(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    group_by: str = Query("day", description="Group by: day, week, month", regex="^(day|week|month)$")
) -> Dict[str, Any]:
    """
    Get user statistics including registrations over time and status distribution.
    
    Returns:
    - Registration trends over time
    - User status distribution
    - Geographic distribution (if available)
    - Activity patterns
    """
    # Permission already checked by dependency
    
    # Check cache
    cache_key = f"user_stats_{days}_{group_by}"
    cached_data = analytics_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Registration trends
    if group_by == "day":
        date_format = func.date(User.registration_date)
        interval_days = 1
    elif group_by == "week":
        date_format = func.date(func.date_sub(User.registration_date, func.interval(func.dayofweek(User.registration_date) - 1, 'DAY')))
        interval_days = 7
    else:  # month
        date_format = func.date_format(User.registration_date, '%Y-%m-01')
        interval_days = 30
    
    registrations = db.query(
        date_format.label('period'),
        func.count(User.id).label('count')
    ).filter(
        User.registration_date >= start_date
    ).group_by('period').order_by('period').all()
    
    # Convert to list of dicts
    registration_trend = [
        {"date": str(r.period), "count": r.count}
        for r in registrations
    ]
    
    # User status distribution
    status_distribution = db.query(
        User.status,
        func.count(User.id).label('count')
    ).group_by(User.status).all()
    
    status_data = {
        status.value: count for status, count in status_distribution
    }
    
    # Activity patterns (interactions by hour of day)
    hourly_activity = db.query(
        extract('hour', AssistantInteraction.interaction_timestamp).label('hour'),
        func.count(AssistantInteraction.id).label('count')
    ).filter(
        AssistantInteraction.interaction_timestamp >= start_date
    ).group_by('hour').order_by('hour').all()
    
    activity_by_hour = {
        int(hour): count for hour, count in hourly_activity
    }
    
    # Fill missing hours with 0
    for hour in range(24):
        if hour not in activity_by_hour:
            activity_by_hour[hour] = 0
    
    # User engagement metrics
    engaged_users = db.query(func.count(func.distinct(AssistantInteraction.user_id))).filter(
        AssistantInteraction.interaction_timestamp >= start_date
    ).scalar()
    
    result = {
        "registration_trend": registration_trend,
        "status_distribution": status_data,
        "activity_patterns": {
            "hourly": [{"hour": h, "count": activity_by_hour[h]} for h in sorted(activity_by_hour.keys())],
            "engaged_users": engaged_users,
            "engagement_rate": round((engaged_users / total_users * 100), 2) if (total_users := db.query(func.count(User.id)).scalar()) > 0 else 0
        },
        "period": {
            "days": days,
            "group_by": group_by,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat()
        }
    }
    
    # Cache the result
    analytics_cache.set(cache_key, result)
    
    return result


@router.get("/responses/stats")
async def get_response_statistics(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get response statistics including completion rates and distress analysis.
    
    Returns:
    - Response completion rates
    - Distress check results
    - Severity distribution
    - Response patterns over time
    """
    # Permission already checked by dependency
    
    # Check cache
    cache_key = f"response_stats_{days}"
    cached_data = analytics_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Get all responses in period
    responses_query = db.query(Response).filter(
        Response.response_timestamp >= start_date
    )
    
    # Distress check statistics
    distress_responses = responses_query.filter(
        Response.question_type == 'distress_check'
    )
    
    distress_yes = distress_responses.filter(Response.response_value == 'yes').count()
    distress_no = distress_responses.filter(Response.response_value == 'no').count()
    total_distress = distress_yes + distress_no
    
    # Severity rating distribution
    severity_distribution = db.query(
        Response.response_value,
        func.count(Response.id).label('count')
    ).filter(
        Response.response_timestamp >= start_date,
        Response.question_type == 'severity_rating'
    ).group_by(Response.response_value).all()
    
    severity_data = {
        int(value): count for value, count in severity_distribution
    }
    
    # Ensure all severity levels are present
    for i in range(1, 6):
        if i not in severity_data:
            severity_data[i] = 0
    
    # Response patterns by day of week
    dow_responses = db.query(
        func.dayname(Response.response_timestamp).label('day'),
        func.count(Response.id).label('count')
    ).filter(
        Response.response_timestamp >= start_date
    ).group_by('day').all()
    
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    response_by_dow = {day: 0 for day in days_of_week}
    for day, count in dow_responses:
        if day in response_by_dow:
            response_by_dow[day] = count
    
    # Calculate completion rate (users who completed both questions)
    users_with_distress = db.query(func.distinct(Response.user_id)).filter(
        Response.response_timestamp >= start_date,
        Response.question_type == 'distress_check'
    ).subquery()
    
    users_with_severity = db.query(func.distinct(Response.user_id)).filter(
        Response.response_timestamp >= start_date,
        Response.question_type == 'severity_rating'
    ).subquery()
    
    users_completed_both = db.query(func.count(func.distinct(Response.user_id))).filter(
        Response.response_timestamp >= start_date,
        Response.user_id.in_(users_with_distress),
        Response.user_id.in_(users_with_severity)
    ).scalar()
    
    total_responding_users = db.query(func.count(func.distinct(Response.user_id))).filter(
        Response.response_timestamp >= start_date
    ).scalar()
    
    completion_rate = (users_completed_both / total_responding_users * 100) if total_responding_users > 0 else 0
    
    result = {
        "distress_analysis": {
            "total_responses": total_distress,
            "distress_yes": distress_yes,
            "distress_no": distress_no,
            "distress_percentage": round((distress_yes / total_distress * 100), 2) if total_distress > 0 else 0
        },
        "severity_distribution": [
            {"level": level, "count": severity_data[level]}
            for level in sorted(severity_data.keys())
        ],
        "response_patterns": {
            "by_day_of_week": [
                {"day": day, "count": response_by_dow[day]}
                for day in days_of_week
            ],
            "completion_rate": round(completion_rate, 2),
            "total_responding_users": total_responding_users,
            "users_completed_both": users_completed_both
        },
        "period": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat()
        }
    }
    
    # Cache the result
    analytics_cache.set(cache_key, result)
    
    return result


@router.get("/severity-trends")
async def get_severity_trends(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    user_id: Optional[int] = Query(None, description="Filter by specific user ID")
) -> Dict[str, Any]:
    """
    Get severity trends over time.
    
    Returns:
    - Average severity by period
    - Severity level changes over time
    - Correlation with distress responses
    - Individual vs population trends
    """
    # Permission already checked by dependency
    
    # Check cache
    cache_key = f"severity_trends_{days}_{user_id or 'all'}"
    cached_data = analytics_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Base query for severity ratings
    base_query = db.query(Response).filter(
        Response.response_timestamp >= start_date,
        Response.question_type == 'severity_rating'
    )
    
    if user_id:
        base_query = base_query.filter(Response.user_id == user_id)
    
    # Daily average severity
    daily_severity = db.query(
        func.date(Response.response_timestamp).label('date'),
        func.avg(func.cast(Response.response_value, Integer)).label('avg_severity'),
        func.count(Response.id).label('response_count')
    ).filter(
        Response.response_timestamp >= start_date,
        Response.question_type == 'severity_rating'
    )
    
    if user_id:
        daily_severity = daily_severity.filter(Response.user_id == user_id)
    
    daily_severity = daily_severity.group_by('date').order_by('date').all()
    
    severity_timeline = [
        {
            "date": str(row.date),
            "average_severity": round(float(row.avg_severity), 2),
            "response_count": row.response_count
        }
        for row in daily_severity
    ]
    
    # Severity level transitions (how users move between severity levels)
    if not user_id:
        # Get pairs of consecutive responses for each user
        transitions = defaultdict(lambda: defaultdict(int))
        
        users_with_multiple = db.query(Response.user_id).filter(
            Response.response_timestamp >= start_date,
            Response.question_type == 'severity_rating'
        ).group_by(Response.user_id).having(func.count(Response.id) > 1).all()
        
        for (uid,) in users_with_multiple:
            user_responses = db.query(Response).filter(
                Response.user_id == uid,
                Response.response_timestamp >= start_date,
                Response.question_type == 'severity_rating'
            ).order_by(Response.response_timestamp).all()
            
            for i in range(len(user_responses) - 1):
                from_level = int(user_responses[i].response_value)
                to_level = int(user_responses[i + 1].response_value)
                transitions[from_level][to_level] += 1
    
        # Convert transitions to list format
        transition_matrix = []
        for from_level in range(1, 6):
            for to_level in range(1, 6):
                count = transitions[from_level][to_level]
                if count > 0:
                    transition_matrix.append({
                        "from": from_level,
                        "to": to_level,
                        "count": count
                    })
    else:
        transition_matrix = []
    
    # Correlation with distress (average severity when distress is yes vs no)
    distress_correlation = db.query(
        Response.response_value.label('distress'),
        func.avg(
            case(
                (Response.question_type == 'severity_rating', func.cast(Response.response_value, Integer)),
                else_=None
            )
        ).label('avg_severity')
    ).select_from(Response).join(
        db.query(
            Response.user_id,
            Response.response_value,
            func.date(Response.response_timestamp).label('date')
        ).filter(
            Response.question_type == 'distress_check',
            Response.response_timestamp >= start_date
        ).subquery(),
        and_(
            Response.user_id == Response.user_id,
            func.date(Response.response_timestamp) == func.date(Response.response_timestamp)
        )
    ).filter(
        Response.question_type == 'severity_rating',
        Response.response_timestamp >= start_date
    ).group_by('distress').all()
    
    distress_severity_correlation = {
        row.distress: round(float(row.avg_severity), 2) if row.avg_severity else 0
        for row in distress_correlation
    }
    
    # Overall statistics
    overall_stats = db.query(
        func.avg(func.cast(Response.response_value, Integer)).label('avg'),
        func.min(func.cast(Response.response_value, Integer)).label('min'),
        func.max(func.cast(Response.response_value, Integer)).label('max'),
        func.stddev(func.cast(Response.response_value, Integer)).label('std_dev')
    ).filter(
        Response.response_timestamp >= start_date,
        Response.question_type == 'severity_rating'
    )
    
    if user_id:
        overall_stats = overall_stats.filter(Response.user_id == user_id)
    
    stats = overall_stats.first()
    
    result = {
        "severity_timeline": severity_timeline,
        "transitions": transition_matrix if not user_id else [],
        "distress_correlation": distress_severity_correlation,
        "overall_statistics": {
            "average": round(float(stats.avg), 2) if stats.avg else 0,
            "min": int(stats.min) if stats.min else 0,
            "max": int(stats.max) if stats.max else 0,
            "std_deviation": round(float(stats.std_dev), 2) if stats.std_dev else 0
        },
        "filters": {
            "user_id": user_id,
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat()
        }
    }
    
    # Cache the result
    analytics_cache.set(cache_key, result)
    
    return result


@router.post("/cache/clear")
async def clear_analytics_cache(
    current_admin: AdminUser = Depends(require_admin)
) -> Dict[str, str]:
    """
    Clear the analytics cache.
    
    Requires admin permission.
    """
    # Permission already checked by dependency
    
    analytics_cache.clear()
    
    return {"message": "Analytics cache cleared successfully"}


@router.get("/recent-activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer),
    limit: int = Query(10, description="Number of activities to return", ge=1, le=50)
) -> Dict[str, Any]:
    """
    Get recent system activity including new users, responses, and admin actions.
    """
    from admin.models.admin import AuditLog
    
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
    
    # Get recent users
    recent_users = db.query(User).order_by(
        User.registration_date.desc()
    ).limit(5).all()
    
    # Get recent admin actions
    recent_admin_actions = db.query(
        AuditLog.id,
        AuditLog.action,
        AuditLog.resource_type,
        AuditLog.resource_id,
        AuditLog.timestamp,
        AdminUser.username
    ).join(AdminUser).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
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
    
    # Add new users from last 24 hours
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    for u in recent_users:
        if u.registration_date >= yesterday:
            activities.append({
                "type": "new_user",
                "timestamp": u.registration_date,
                "text": f"New user registered: {u.first_name} {u.family_name or ''}",
                "icon": "👤",
                "user_id": u.id,
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