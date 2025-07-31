"""
Main FastAPI application module for the admin panel.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

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

# Debug endpoint
@app.get("/debug")
async def debug_info():
    """Debug endpoint to check server status."""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database_url": SQLALCHEMY_DATABASE_URL[:50] + "...",
        "timestamp": datetime.utcnow().isoformat()
    }

# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # For non-API routes, return HTML error page
    context = create_template_context(request, {
        "error_code": exc.status_code,
        "error_message": exc.detail
    })
    return templates.TemplateResponse(
        "error.html",
        context,
        status_code=exc.status_code
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    context = create_template_context(request, {
        "error_code": 500,
        "error_message": "Internal server error"
    })
    return templates.TemplateResponse(
        "error.html",
        context,
        status_code=500
    )


# Root route
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main dashboard."""
    context = create_template_context(request, {
        "page_title": "Dashboard"
    })
    return templates.TemplateResponse("dashboard.html", context)


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