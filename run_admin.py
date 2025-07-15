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
import sys
import argparse
import logging
from pathlib import Path

# Add project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from admin.core.config import settings


def setup_logging(log_level: str = "info"):
    """
    Configure logging for the admin server.
    
    Args:
        log_level: Logging level (debug, info, warning, error)
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(numeric_level)
    logging.getLogger("uvicorn.error").setLevel(numeric_level)
    logging.getLogger("uvicorn.access").setLevel(numeric_level)
    
    # In production, reduce verbosity of some loggers
    if settings.is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("multipart").setLevel(logging.WARNING)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the Diabetes Monitoring Admin Panel",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=settings.ADMIN_HOST,
        help="Host to bind the server to"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.ADMIN_PORT,
        help="Port to bind the server to"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.is_development,
        help="Enable auto-reload (development mode)"
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
        help="Number of worker processes (ignored if --reload is set)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error"],
        default="debug" if settings.is_development else "info",
        help="Logging level"
    )
    
    parser.add_argument(
        "--access-log",
        action="store_true",
        default=True,
        help="Enable access log"
    )
    
    parser.add_argument(
        "--no-access-log",
        dest="access_log",
        action="store_false",
        help="Disable access log"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for running the admin server."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Log startup information
    logger.info("=" * 60)
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Server: http://{args.host}:{args.port}")
    logger.info(f"API Docs: http://{args.host}:{args.port}/api/docs")
    logger.info(f"Auto-reload: {'enabled' if args.reload else 'disabled'}")
    logger.info("=" * 60)
    
    # Validate settings before starting
    try:
        from admin.core.config import validate_settings
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
    if settings.is_production:
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