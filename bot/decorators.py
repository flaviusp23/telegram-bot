"""Decorators for the diabetes monitoring bot."""
import functools
import logging
from datetime import datetime
from time import time
from typing import Callable, Optional, TypeVar, ParamSpec

from telegram import Update
from telegram.ext import ContextTypes

from bot_config.bot_constants import BotMessages
from config import ADMIN_TELEGRAM_IDS, IS_DEVELOPMENT
from database import get_user_by_telegram_id, db_session_context
from database.models import User

# Type definitions
P = ParamSpec('P')
T = TypeVar('T')

logger = logging.getLogger(__name__)


def with_user_context(func: Callable) -> Callable:
    """Decorator that provides user context without requiring registration."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        telegram_id = str(update.effective_user.id)
        
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            # Pass user (can be None) to the wrapped function
            return await func(update, context, user, *args, **kwargs)
    
    return wrapper


def require_registered_user(func: Callable) -> Callable:
    """Decorator to ensure user is registered before accessing a command."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        telegram_id = str(update.effective_user.id)
        
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            
            if not user:
                await update.message.reply_text(BotMessages.PLEASE_REGISTER_FIRST)
                return
            
            # Pass user to the wrapped function
            return await func(update, context, user, *args, **kwargs)
    
    return wrapper


def admin_only(telegram_ids: Optional[list] = None):
    """Decorator to restrict access to admin users only."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = str(update.effective_user.id)
            allowed_ids = telegram_ids or ADMIN_TELEGRAM_IDS
            
            if user_id not in allowed_ids:
                await update.message.reply_text(BotMessages.ADMIN_ONLY_ACCESS)
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def update_last_interaction(func: Callable) -> Callable:
    """Decorator to update user's last interaction timestamp."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, *args, **kwargs):
        # Update last interaction
        with db_session_context() as db:
            db_user = db.query(User).filter(User.id == user.id).first()
            if db_user:
                db_user.last_interaction = datetime.utcnow()
        
        return await func(update, context, user, *args, **kwargs)
    
    return wrapper


def log_command_usage(func: Callable) -> Callable:
    """Decorator to log command usage."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        command = update.message.text if update.message else "Unknown"
        
        logger.info(f"Command '{command}' used by user {user.id} ({user.username or 'No username'})")
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def rate_limit(max_calls: int = 5, period_seconds: int = 60):
    """Rate limiting decorator to prevent spam."""
    user_calls = {}
    
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            # Skip rate limiting in development
            if IS_DEVELOPMENT:
                return await func(update, context, *args, **kwargs)
            
            user_id = str(update.effective_user.id)
            current_time = time()
            
            # Initialize or clean old calls
            if user_id not in user_calls:
                user_calls[user_id] = []
            
            # Remove old calls outside the time window
            user_calls[user_id] = [
                call_time for call_time in user_calls[user_id]
                if current_time - call_time < period_seconds
            ]
            
            # Check rate limit
            if len(user_calls[user_id]) >= max_calls:
                await update.message.reply_text(BotMessages.RATE_LIMIT_EXCEEDED)
                return
            
            # Record this call
            user_calls[user_id].append(current_time)
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator