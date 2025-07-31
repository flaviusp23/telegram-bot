#!/usr/bin/env python3
"""
Run the Admin backend server with uvicorn.

This script provides a convenient way to start the admin panel with proper
Python path configuration and command-line arguments for development.

Usage examples:
    # Run with default settings (from .env)
    ./run_admin.py
    
    # Run on a specific host and port
    ./run_admin.py --host 0.0.0.0 --port 8080
    
    # Run in production mode without auto-reload
    ./run_admin.py --no-reload --workers 4
    
    # Run with debug logging
    ./run_admin.py --log-level debug
    
    # Show all available options
    ./run_admin.py --help
"""
from pathlib import Path
import argparse
import logging
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

import uvicorn

from admin.core.config import settings


def validate_settings():
    """Validate required settings are present."""
    required = ['DB_HOST', 'DB_USER', 'DB_NAME', 'SECRET_KEY']
    missing = []
    
    for setting in required:
        if not getattr(settings, setting, None):
            missing.append(setting)
    
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")


def main():
    """Main entry point for the admin server."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run the diabetes monitoring admin panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--host",
        default=settings.ADMIN_HOST,
        help=f"Host to bind to (default: {settings.ADMIN_HOST})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.actual_port,
        help=f"Port to bind to (default: {settings.actual_port})"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.ENVIRONMENT.lower() == "dev",
        help="Enable auto-reload (default: enabled in dev mode)"
    )
    
    parser.add_argument(
        "--no-reload",
        dest="reload",
        action="store_false",
        help="Disable auto-reload"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Logging level (default: info)"
    )
    
    parser.add_argument(
        "--access-log",
        action="store_true",
        default=True,
        help="Enable access log (default: enabled)"
    )
    
    parser.add_argument(
        "--no-access-log",
        dest="access_log",
        action="store_false",
        help="Disable access log"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting admin panel on {args.host}:{args.port}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Validate settings
    try:
        validate_settings()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your environment variables and .env file")
        sys.exit(1)
    
    # Configure uvicorn
    uvicorn_config = {
        "app": "admin.main:app",
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "log_level": args.log_level,
        "access_log": args.access_log,
    }
    
    # Add workers only if not in reload mode
    if not args.reload and args.workers > 1:
        uvicorn_config["workers"] = args.workers
        logger.info(f"Running with {args.workers} workers")
    
    # Add reload directories in development mode
    if args.reload:
        uvicorn_config["reload_dirs"] = ["admin", "bot"]
        uvicorn_config["reload_delay"] = 0.25
        logger.info("Watching directories: admin, bot")
    
    # Additional production configurations
    if settings.ENVIRONMENT.lower() == "prod":
        # Use production-ready server settings
        uvicorn_config.update({
            "loop": "uvloop",  # Use uvloop for better performance
            "http": "httptools",  # Use httptools for better HTTP parsing
            "ws": "websockets",  # WebSocket support
            "lifespan": "on",  # Enable lifespan events
            "interface": "asgi3",  # Use ASGI3 interface
            "proxy_headers": True,  # Trust proxy headers (for reverse proxy)
            "forwarded_allow_ips": "*",  # Allow all IPs for proxy headers
        })
        logger.info("Using production server configuration")
    
    try:
        # Run the server
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()