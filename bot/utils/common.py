"""Common utility functions for the bot.

This module contains reusable utility functions to reduce code duplication
and standardize common patterns across the bot.
"""
from functools import wraps
from typing import Optional, Any, Callable, TypeVar, ParamSpec
import logging

from telegram import Update
from telegram.error import Forbidden, BadRequest
from telegram.ext import ContextTypes

from bot_config.bot_constants import BotMessages, LogMessages
from database import db_session_context, get_user_by_telegram_id
from database.models import User, UserStatus

logger = logging.getLogger(__name__)

# Type variables for better type hints
P = ParamSpec('P')
R = TypeVar('R')


class BotError(Exception):
    """Base exception for bot-specific errors"""
    pass


class UserNotFoundError(BotError):
    """Raised when a user is not found in the database"""
    pass


class MessageSendError(BotError):
    """Raised when a message fails to send"""
    pass


async def send_error_message(update: Update, message: str) -> None:
    """Send an error message to the user.
    
    Args:
        update: The telegram update object
        message: The error message to send
    """
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(message)
        elif update.message:
            await update.message.reply_text(message)
        else:
            logger.error("No valid message or callback query to reply to")
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


async def get_user_from_update(update: Update) -> Optional[User]:
    """Extract user from update with proper error handling.
    
    Args:
        update: The telegram update object
        
    Returns:
        User object if found, None otherwise
    """
    telegram_user = update.effective_user
    if not telegram_user:
        logger.error("No effective user found in update")
        return None
    
    telegram_id = str(telegram_user.id)
    
    with db_session_context(commit=False) as db:
        return get_user_by_telegram_id(db, telegram_id)


def with_error_handling(
    error_message: str = BotMessages.ERROR_GENERIC,
    log_errors: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that provides consistent error handling for bot commands.
    
    Args:
        error_message: Message to send to user on error
        log_errors: Whether to log errors
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: P.args, **kwargs: P.kwargs) -> Optional[R]:
            try:
                return await func(update, context, *args, **kwargs)
            except UserNotFoundError:
                await send_error_message(update, BotMessages.ERROR_USER_NOT_FOUND)
                return None
            except MessageSendError as e:
                if log_errors:
                    logger.error(f"{func.__name__} failed with MessageSendError: {e}")
                return None
            except Exception as e:
                if log_errors:
                    logger.error(f"{func.__name__} failed with error: {e}", exc_info=True)
                await send_error_message(update, error_message)
                return None
        return wrapper
    return decorator


def with_database_transaction(commit: bool = True) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that provides database session management.
    
    Args:
        commit: Whether to commit the transaction
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with db_session_context(commit=commit) as db:
                kwargs['db'] = db
                return await func(*args, **kwargs)
        return wrapper
    return decorator


async def handle_blocked_user(user: User) -> None:
    """Update user status when they block the bot.
    
    Args:
        user: The user who blocked the bot
    """
    with db_session_context() as db:
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            db_user.status = UserStatus.blocked
            logger.info(LogMessages.USER_STATUS_UPDATED.format(telegram_id=user.telegram_id))


def validate_user_context(context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """Validate and retrieve user_id from context.
    
    Args:
        context: The telegram context
        
    Returns:
        User ID if found, None otherwise
    """
    user_id = context.user_data.get('user_id')
    if not user_id:
        logger.error("No user_id found in context")
    return user_id


def create_keyboard_rows(buttons: list[tuple[str, str]], columns: int = 3) -> list[list[tuple[str, str]]]:
    """Create keyboard button rows with specified number of columns.
    
    Args:
        buttons: List of (text, callback_data) tuples
        columns: Number of buttons per row
        
    Returns:
        List of button rows
    """
    rows = []
    for i in range(0, len(buttons), columns):
        rows.append(buttons[i:i + columns])
    return rows


async def safe_message_send(
    bot: Any,
    chat_id: str,
    text: str,
    **kwargs
) -> bool:
    """Safely send a message with error handling.
    
    Args:
        bot: The bot instance
        chat_id: The chat ID to send to
        text: The message text
        **kwargs: Additional arguments for send_message
        
    Returns:
        True if message sent successfully, False otherwise
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return True
    except Forbidden:
        logger.warning(f"User {chat_id} has blocked the bot")
        return False
    except BadRequest as e:
        logger.error(f"Bad request sending message to {chat_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        return False