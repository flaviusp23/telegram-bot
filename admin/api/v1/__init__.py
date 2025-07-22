"""
API v1 router aggregation module.
"""
from fastapi import APIRouter

# Create the main v1 router
router = APIRouter()

# Import and include individual route modules here
from admin.api.v1 import auth, users, analytics, export, audit

# Include the auth router (prefix already defined in auth.py)
router.include_router(auth.router)
# Include the users router
router.include_router(users.router, prefix="/users", tags=["patients"])
# Include the analytics router
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
# Include the export router
router.include_router(export.router, prefix="/export", tags=["export"])
# Include the audit router
router.include_router(audit.router, prefix="/audit", tags=["audit"])

# You can also add version-specific endpoints here
@router.get("/")
async def api_v1_root():
    """API v1 root endpoint."""
    return {
        "message": "Welcome to API v1",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "auth": {
                "login": "/api/v1/auth/login",
                "refresh": "/api/v1/auth/refresh",
                "logout": "/api/v1/auth/logout",
                "me": "/api/v1/auth/me",
                "change-password": "/api/v1/auth/change-password"
            },
            "patients": {
                "list": "GET /api/v1/users",
                "get": "GET /api/v1/users/{id}",
                "update": "PUT /api/v1/users/{id}",
                "block": "POST /api/v1/users/{id}/block",
                "unblock": "POST /api/v1/users/{id}/unblock",
                "responses": "GET /api/v1/users/{id}/responses"
            },
            "analytics": {
                "dashboard": "GET /api/v1/analytics/dashboard",
                "patient_stats": "GET /api/v1/analytics/users/stats",
                "response_stats": "GET /api/v1/analytics/responses/stats",
                "severity_trends": "GET /api/v1/analytics/severity-trends",
                "clear_cache": "POST /api/v1/analytics/cache/clear"
            }
        }
    }

@router.get("/health")
async def api_v1_health():
    """API v1 health check."""
    return {"status": "healthy", "api_version": "v1"}