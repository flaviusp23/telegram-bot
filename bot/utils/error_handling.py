"""Standardized error handling for the bot.

This module provides consistent error handling patterns across the bot,
including custom exceptions, error decorators, and error response utilities.
"""
from functools import wraps
from typing import Callable, Optional, TypeVar, ParamSpec
import logging

from telegram import Update
from telegram.error import TelegramError, Forbidden, BadRequest, NetworkError
from telegram.ext import ContextTypes

from bot_config.bot_constants import BotMessages

logger = logging.getLogger(__name__)

# Type variables
P = ParamSpec('P')
R = TypeVar('R')


# Custom Exceptions
class BotException(Exception):
    """Base exception for all bot-specific errors."""


class UserException(BotException):
    """Base exception for user-related errors."""


class UserNotRegisteredException(UserException):
    """Raised when an unregistered user tries to access restricted features."""


class UserBlockedException(UserException):
    """Raised when trying to send message to a user who blocked the bot."""


class DataException(BotException):
    """Base exception for data-related errors."""


class DatabaseException(DataException):
    """Raised when database operations fail."""


class ValidationException(DataException):
    """Raised when data validation fails."""


class ExternalServiceException(BotException):
    """Raised when external service calls fail."""


# Error Response Functions
async def send_user_error(
    update: Update,
    error_type: str = "generic",
    custom_message: Optional[str] = None
) -> None:
    """Send appropriate error message to user based on error type.
    
    Args:
        update: Telegram update object
        error_type: Type of error (generic, registration, database, etc.)
        custom_message: Optional custom error message
    """
    error_messages = {
        "generic": BotMessages.ERROR_GENERIC,
        "registration": BotMessages.NOT_REGISTERED,
        "database": BotMessages.ERROR_RECORDING_RESPONSE,
        "user_not_found": BotMessages.ERROR_USER_NOT_FOUND,
        "rate_limit": BotMessages.RATE_LIMIT_EXCEEDED,
    }
    
    message = custom_message or error_messages.get(error_type, BotMessages.ERROR_GENERIC)
    
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(message)
        elif update.message:
            await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


# Error Handling Decorators
def handle_telegram_errors(
    log_errors: bool = True,
    send_error_to_user: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to handle Telegram-specific errors.
    
    Args:
        log_errors: Whether to log errors
        send_error_to_user: Whether to send error message to user
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(
            update: Update, 
            context: ContextTypes.DEFAULT_TYPE, 
            *args: P.args, 
            **kwargs: P.kwargs
        ) -> Optional[R]:
            try:
                return await func(update, context, *args, **kwargs)
            
            except Forbidden as e:
                if log_errors:
                    logger.warning(f"User blocked bot in {func.__name__}: {e}")
                # Don't send message since user blocked us
                return None
            
            except BadRequest as e:
                if log_errors:
                    logger.error(f"Bad request in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(update, "generic")
                return None
            
            except NetworkError as e:
                if log_errors:
                    logger.error(f"Network error in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(
                        update, 
                        custom_message="Network error. Please try again later."
                    )
                return None
            
            except TelegramError as e:
                if log_errors:
                    logger.error(f"Telegram error in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(update, "generic")
                return None
            
        return wrapper
    return decorator


def handle_database_errors(
    rollback: bool = True,
    send_error_to_user: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to handle database-related errors.
    
    Args:
        rollback: Whether to rollback transaction on error
        send_error_to_user: Whether to send error message to user
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(
            update: Update, 
            context: ContextTypes.DEFAULT_TYPE, 
            *args: P.args, 
            **kwargs: P.kwargs
        ) -> Optional[R]:
            try:
                return await func(update, context, *args, **kwargs)
            
            except DatabaseException as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(update, "database")
                return None
            
            except Exception as e:
                # Check if it's a SQLAlchemy error
                if "sqlalchemy" in str(type(e)).lower():
                    logger.error(f"SQLAlchemy error in {func.__name__}: {e}")
                    if send_error_to_user:
                        await send_user_error(update, "database")
                    return None
                # Re-raise if not database-related
                raise
            
        return wrapper
    return decorator


def handle_all_errors(
    error_message: Optional[str] = None,
    log_errors: bool = True,
    send_error_to_user: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Comprehensive error handler decorator.
    
    Args:
        error_message: Custom error message
        log_errors: Whether to log errors
        send_error_to_user: Whether to send error message to user
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(
            update: Update, 
            context: ContextTypes.DEFAULT_TYPE, 
            *args: P.args, 
            **kwargs: P.kwargs
        ) -> Optional[R]:
            try:
                return await func(update, context, *args, **kwargs)
            
            # Handle specific exceptions
            except UserNotRegisteredException:
                if send_error_to_user:
                    await send_user_error(update, "registration")
                return None
            
            except UserBlockedException as e:
                if log_errors:
                    logger.warning(f"User blocked bot: {e}")
                return None
            
            except ValidationException as e:
                if log_errors:
                    logger.error(f"Validation error in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(
                        update, 
                        custom_message=str(e) or "Invalid input. Please try again."
                    )
                return None
            
            except DatabaseException as e:
                if log_errors:
                    logger.error(f"Database error in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(update, "database")
                return None
            
            except BotException as e:
                if log_errors:
                    logger.error(f"Bot error in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(update, "generic", error_message)
                return None
            
            # Handle Telegram errors
            except TelegramError as e:
                if log_errors:
                    logger.error(f"Telegram error in {func.__name__}: {e}")
                if send_error_to_user:
                    await send_user_error(update, "generic", error_message)
                return None
            
            # Catch all other exceptions
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"Unexpected error in {func.__name__}: {e}", 
                        exc_info=True
                    )
                if send_error_to_user:
                    await send_user_error(update, "generic", error_message)
                return None
            
        return wrapper
    return decorator


# Context managers for error handling
class ErrorHandler:
    """Context manager for handling errors in async blocks."""
    
    def __init__(
        self, 
        update: Update, 
        error_type: str = "generic",
        log_errors: bool = True,
        send_error_to_user: bool = True
    ):
        self.update = update
        self.error_type = error_type
        self.log_errors = log_errors
        self.send_error_to_user = send_error_to_user
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        if self.log_errors:
            logger.error(f"Error in context: {exc_val}", exc_info=True)
        
        if self.send_error_to_user:
            await send_user_error(self.update, self.error_type)
        
        # Suppress the exception
        return True