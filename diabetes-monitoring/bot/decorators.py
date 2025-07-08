"""Consolidated decorators for the diabetes monitoring bot.

This module merges all decorators from user_decorators.py and db_decorators.py,
resolving duplicate functions and providing a unified interface.

Naming conventions:
- Variables: snake_case
  - user (for user objects)
  - telegram_id (not telegramId)
- Function parameters: Descriptive names in snake_case
"""
import functools
import logging
from typing import Callable, Any, Optional, TypeVar, ParamSpec
from telegram import Update
from telegram.ext import ContextTypes

from database import get_user_by_telegram_id, db_session_context
from database.models import User
from bot_config.bot_constants import BotMessages

logger = logging.getLogger(__name__)

# Type variables for better type hints
P = ParamSpec('P')
R = TypeVar('R')
T = TypeVar('T')


def require_registered_user(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that ensures the user is registered before executing the function.
    
    This decorator:
    1. Extracts the telegram_id from the update
    2. Checks if the user exists in the database
    3. If not registered, sends an error message and returns
    4. If registered, passes the user object to the decorated function
    
    The decorated function must accept 'user' as a keyword argument.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: P.args, **kwargs: P.kwargs) -> Optional[R]:
        # Extract telegram user info
        telegram_user = update.effective_user
        if not telegram_user:
            logger.error("No effective user found in update")
            return None
            
        telegram_id = str(telegram_user.id)
        
        # Check if user is registered
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            if not user:
                # Determine which message to use based on the function
                if func.__name__ == 'questionnaire':
                    message = BotMessages.PLEASE_REGISTER_FIRST
                else:
                    message = BotMessages.NOT_REGISTERED
                    
                await update.message.reply_text(message)
                return None
            
            # Pass the user object to the decorated function
            kwargs['user'] = user
            return await func(update, context, *args, **kwargs)
    
    return wrapper


def with_db_user(
    send_error_message: bool = True,
    error_message: Optional[str] = None
) -> Callable:
    """
    Decorator that ensures the user is registered before allowing access to a command.
    Automatically fetches the user from the database and passes it to the function.
    
    This is the db_decorators version of require_registered_user, kept for compatibility
    and advanced use cases with custom error messages.
    
    Args:
        send_error_message: Whether to send an error message if user is not registered
        error_message: Custom error message (defaults to BotMessages.NOT_REGISTERED)
    
    The decorated function will receive the database user as 'user' in kwargs.
    
    Example:
        @with_db_user()
        async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user=None):
            # user is automatically populated with the User object
            await update.message.reply_text(f"Hello {user.first_name}!")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> T:
            user = update.effective_user
            telegram_id = str(user.id)
            
            with db_session_context(commit=False) as db:
                user = get_user_by_telegram_id(db, telegram_id)
                
                if not user:
                    logger.warning(f"Unregistered user attempted to access {func.__name__}: {telegram_id}")
                    if send_error_message:
                        message = error_message or BotMessages.NOT_REGISTERED
                        if update.message:
                            await update.message.reply_text(message)
                        elif update.callback_query:
                            await update.callback_query.answer(message, show_alert=True)
                    return None
                
                # Add user to kwargs
                kwargs['user'] = user
                return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


def with_user_context(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that automatically fetches user and stores in context.
    
    This decorator:
    1. Fetches the user from the database
    2. Stores user info in the context for use by callbacks
    3. Does not require user registration (useful for start command)
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: P.args, **kwargs: P.kwargs) -> R:
        # Extract telegram user info
        telegram_user = update.effective_user
        if telegram_user:
            telegram_id = str(telegram_user.id)
            
            # Try to get user from database
            with db_session_context(commit=False) as db:
                user = get_user_by_telegram_id(db, telegram_id)
                if user:
                    # Store user info in context
                    context.user_data['user_id'] = user.id
                    context.user_data['user_first_name'] = user.first_name
                    context.user_data['user'] = user
                    kwargs['user'] = user
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def admin_only(admin_telegram_ids: Optional[list[str]] = None):
    """
    Decorator that restricts function access to admin users only.
    
    Args:
        admin_telegram_ids: List of telegram IDs that are admins.
                           If None, will check for ADMIN_TELEGRAM_IDS in config.
                           
    Returns:
        The decorator function
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: P.args, **kwargs: P.kwargs) -> Optional[R]:
            # Get admin IDs
            admin_ids = admin_telegram_ids
            if admin_ids is None:
                # Try to import from config
                try:
                    from config import ADMIN_TELEGRAM_IDS
                    admin_ids = ADMIN_TELEGRAM_IDS
                except ImportError:
                    admin_ids = []
            
            # Check if user is admin
            telegram_user = update.effective_user
            if not telegram_user or str(telegram_user.id) not in admin_ids:
                await update.message.reply_text(BotMessages.ADMIN_ONLY_ACCESS)
                return None
                
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


def log_command_usage(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that logs command usage for analytics.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: P.args, **kwargs: P.kwargs) -> R:
        telegram_user = update.effective_user
        command_name = func.__name__
        
        if telegram_user:
            logger.info(f"Command /{command_name} called by user {telegram_user.id} ({telegram_user.first_name})")
        else:
            logger.info(f"Command /{command_name} called (no user info)")
            
        try:
            result = await func(update, context, *args, **kwargs)
            logger.info(f"Command /{command_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Command /{command_name} failed with error: {e}")
            raise
    
    return wrapper


def update_last_interaction(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that updates the user's last interaction timestamp.
    
    This decorator should be used with require_registered_user to ensure
    the user exists.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: P.args, **kwargs: P.kwargs) -> R:
        # Execute the wrapped function first
        result = await func(update, context, *args, **kwargs)
        
        # Update last interaction if user is provided
        if 'user' in kwargs and kwargs['user']:
            user = kwargs['user']
            try:
                from datetime import datetime
                with db_session_context() as db:
                    user_record = db.query(User).filter(User.id == user.id).first()
                    if user_record:
                        user_record.last_interaction = datetime.utcnow()
                        logger.debug(f"Updated last interaction for user {user.telegram_id}")
            except Exception as e:
                logger.error(f"Failed to update last interaction: {e}")
        
        return result
    
    return wrapper


def rate_limit(max_calls: int = 5, period_seconds: int = 60):
    """
    Decorator that implements rate limiting per user.
    
    Args:
        max_calls: Maximum number of calls allowed within the period
        period_seconds: Time period in seconds
        
    Returns:
        The decorator function
    """
    # Store call times per user
    user_calls: dict[str, list[float]] = {}
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: P.args, **kwargs: P.kwargs) -> Optional[R]:
            from time import time
            
            # Skip rate limiting in development mode
            try:
                from config import IS_DEVELOPMENT
                if IS_DEVELOPMENT:
                    return await func(update, context, *args, **kwargs)
            except ImportError:
                pass
            
            # Get user ID
            telegram_user = update.effective_user
            if not telegram_user:
                return await func(update, context, *args, **kwargs)
                
            user_id = str(telegram_user.id)
            current_time = time()
            
            # Initialize user's call list if needed
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
                return None
            
            # Record this call
            user_calls[user_id].append(current_time)
            
            # Execute function
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


def handle_db_errors(
    error_message: Optional[str] = None,
    log_errors: bool = True
) -> Callable:
    """
    Decorator that handles database errors gracefully.
    
    Args:
        error_message: Custom error message to send to user
        log_errors: Whether to log errors
    
    Example:
        @handle_db_errors(error_message="Failed to save your data")
        async def save_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Database operations here
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> T:
            try:
                return await func(update, context, *args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Database error in {func.__name__}: {e}")
                
                message = error_message or BotMessages.ERROR_GENERIC
                if update.message:
                    await update.message.reply_text(message)
                elif update.callback_query:
                    await update.callback_query.answer(message, show_alert=True)
                    
                return None
        
        return wrapper
    return decorator