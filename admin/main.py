"""
Main FastAPI application module for the admin panel.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import logging
import time

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from jose import JWTError, jwt

from admin.api.v1 import router as api_v1_router
from admin.core.config import settings
from admin.i18n.jinja2 import create_template_context, setup_i18n_jinja2
from admin.i18n.middleware import I18nMiddleware
from database.database import SQLALCHEMY_DATABASE_URL
from admin.middleware.rate_limit import RateLimitMiddleware
from admin.middleware.validation import RequestValidationMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug flag
DEBUG = settings.ENVIRONMENT.lower() == "dev"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    logger.info(f"Starting admin panel in {settings.ENVIRONMENT} mode")
    logger.info(f"Admin URL: http://{settings.ADMIN_HOST}:{settings.actual_port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down admin panel")


# Create FastAPI app
app = FastAPI(
    title="Diabetes Monitoring Admin Panel",
    description="Administrative interface for managing the diabetes monitoring system",
    version="1.0.0",
    lifespan=lifespan,
    debug=DEBUG
)

# Add middleware
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(I18nMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
else:
    logger.warning(f"Static directory not found at {static_path}")

# Setup templates with i18n
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
setup_i18n_jinja2(templates.env)

# Simple health endpoint
@app.get("/ping")
async def ping():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Admin panel is running"}

# Debug endpoint
@app.get("/debug")
async def debug_info():
    """Debug endpoint to check server status."""
    try:
        return {
            "status": "ok",
            "environment": settings.ENVIRONMENT,
            "database_url": SQLALCHEMY_DATABASE_URL[:50] + "...",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    # Always return JSON for now to avoid template issues
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "path": request.url.path}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Always return JSON for now to avoid template issues
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc), "path": request.url.path}
    )


async def check_auth_cookie(request: Request):
    """Check if user is authenticated via cookie/localStorage (for HTML pages)."""
    # Check for auth token in cookies or headers
    token = request.cookies.get("access_token")
    
    if not token:
        # Check Authorization header as fallback
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return None
        
    try:
        # Import here to avoid circular imports
        from admin.core.config import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def require_auth_html(request: Request):
    """Dependency to require authentication for HTML pages."""
    user = await check_auth_cookie(request)
    if not user:
        # Store the original URL to redirect back after login
        return RedirectResponse(url=f"/login?next={request.url.path}", status_code=303)
    return user


# Root route
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main dashboard."""
    # Check authentication
    user = await check_auth_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    context = create_template_context(request)
    context.update({
        "page_title": "Dashboard"
    })
    return templates.TemplateResponse("dashboard.html", context)


# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    context = create_template_context(request)
    context.update({
        "page_title": "Login"
    })
    return templates.TemplateResponse("login.html", context)


# Dashboard route (redirect from root)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Render the dashboard page."""
    # Check authentication
    user = await check_auth_cookie(request)
    if not user:
        return RedirectResponse(url="/login?next=/dashboard", status_code=303)
    
    context = create_template_context(request)
    context.update({
        "page_title": "Dashboard"
    })
    return templates.TemplateResponse("dashboard.html", context)


# Users page route
@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Render the users page."""
    # Check authentication
    user = await check_auth_cookie(request)
    if not user:
        return RedirectResponse(url="/login?next=/users", status_code=303)
    
    context = create_template_context(request)
    context.update({
        "page_title": "Patient Management"
    })
    return templates.TemplateResponse("users.html", context)


# User detail page route
@app.get("/users/{user_id}", response_class=HTMLResponse)
async def user_detail_page(request: Request, user_id: int):
    """Render the user detail page."""
    # Check authentication
    user = await check_auth_cookie(request)
    if not user:
        return RedirectResponse(url=f"/login?next=/users/{user_id}", status_code=303)
    
    context = create_template_context(request)
    context.update({
        "page_title": "Patient Details",
        "user_id": user_id
    })
    return templates.TemplateResponse("user_detail.html", context)


# I18n route
@app.get("/i18n/{language}.json")
async def get_i18n_file(language: str):
    """Serve i18n JSON files."""
    from fastapi.responses import FileResponse
    import os
    
    file_path = Path(__file__).parent / "static" / "i18n" / f"{language}.json"
    if file_path.exists():
        return FileResponse(file_path, media_type="application/json")
    else:
        raise StarletteHTTPException(status_code=404, detail="Language file not found")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT
    }


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "admin.main:app",
        host=settings.ADMIN_HOST,
        port=settings.actual_port,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )