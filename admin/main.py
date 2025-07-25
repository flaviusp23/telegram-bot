"""
Main FastAPI application module for the admin panel.
"""
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import API routers
from admin.api.v1 import router as api_v1_router

# Import configuration
from admin.core.config import settings

# Import middleware
from admin.middleware.rate_limit import RateLimitMiddleware
from admin.middleware.validation import RequestValidationMiddleware
from admin.i18n.middleware import I18nMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from settings
APP_NAME = settings.API_TITLE
APP_VERSION = settings.API_VERSION
DEBUG = settings.is_development
ALLOWED_ORIGINS = settings.get_cors_origins()

# Path configurations
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"Server: {settings.ADMIN_HOST}:{settings.actual_port}")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs" if DEBUG else None,
    redoc_url="/api/redoc" if DEBUG else None,
)

# Add middleware in correct order (outermost to innermost)
# 1. Rate limiting (should be first to prevent abuse)
app.add_middleware(RateLimitMiddleware)

# 2. Request validation and security headers
app.add_middleware(RequestValidationMiddleware)

# 3. Internationalization middleware
app.add_middleware(I18nMiddleware, default_language="en")

# 4. CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize templates with i18n support
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Setup i18n for templates - both global and context-based approaches
from admin.i18n.jinja2 import setup_i18n_jinja2
setup_i18n_jinja2(templates.env)


# Basic HTML routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the home page."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Home"})
    return templates.TemplateResponse("index.html", context)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Serve the login page."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Login"})
    return templates.TemplateResponse("login.html", context)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Dashboard"})
    return templates.TemplateResponse("dashboard.html", context)


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Serve the patients management page."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Patient Management"})
    return templates.TemplateResponse("users.html", context)


@app.get("/user", response_class=HTMLResponse)
async def user_detail_page(request: Request):
    """Serve the patient detail page (legacy URL for compatibility)."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Patient Details"})
    return templates.TemplateResponse("user_detail.html", context)


@app.get("/patient", response_class=HTMLResponse)
async def patient_detail_page(request: Request):
    """Serve the patient detail page."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Patient Details"})
    return templates.TemplateResponse("user_detail.html", context)


@app.get("/patient-report", response_class=HTMLResponse)
async def patient_report_page(request: Request):
    """Serve the patient report page."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Patient Report"})
    return templates.TemplateResponse("patient_report.html", context)


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Serve the audit logs page."""
    from admin.i18n.jinja2 import create_template_context
    context = create_template_context(request)
    context.update({"title": "Audit Logs"})
    return templates.TemplateResponse("logs.html", context)


# Include API v1 routes
app.include_router(
    api_v1_router, 
    prefix=settings.API_V1_PREFIX, 
    tags=["api_v1"]
)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }



# Error handlers with consistent format
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with consistent error format."""
    if request.url.path.startswith("/api/"):
        # Consistent JSON error response format for API routes
        error_response = {
            "error": {
                "code": exc.status_code,
                "message": str(exc.detail),
                "type": exc.__class__.__name__
            }
        }

        # Add headers if present (e.g., for rate limiting)
        headers = getattr(exc, "headers", {})

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers=headers
        )
    else:
        # Return HTML error page for web routes
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": exc.status_code,
                "detail": exc.detail
            },
            status_code=exc.status_code
        )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """Handle 404 errors with consistent format."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": 404,
                    "message": "Resource not found",
                    "type": "NotFoundError"
                }
            }
        )
    else:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle 500 errors with consistent format."""
    logger.error(f"Internal server error: {exc}", exc_info=True)

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "type": "InternalServerError"
                }
            }
        )
    else:
        return templates.TemplateResponse(
            "500.html",
            {"request": request},
            status_code=500
        )


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "admin.main:app",
        host=settings.ADMIN_HOST,
        port=settings.actual_port,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )
