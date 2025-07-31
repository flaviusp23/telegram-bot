"""Bot utilities package.

This package provides common utilities for the bot including:
- Common utility functions for reducing code duplication
- Standardized error handling patterns
"""

from bot.utils.common import (
    send_error_message,
    get_user_from_update,
    with_error_handling,
    with_database_transaction,
    handle_blocked_user,
    validate_user_context,
    create_keyboard_rows
)
from bot.utils.error_handling import (
    BotException,
    UserException,
    UserNotRegisteredException,
    UserBlockedException,
    DataException,
    DatabaseException,
    ValidationException,
    ExternalServiceException,
    send_user_error,
    handle_telegram_errors,
    handle_database_errors,
    handle_all_errors,
    ErrorHandler
)

__all__ = [
    # Common utilities
    'send_error_message',
    'get_user_from_update',
    'with_error_handling',
    'with_database_transaction',
    'handle_blocked_user',
    'validate_user_context',
    'create_keyboard_rows',
    
    # Error handling
    'BotException',
    'UserException',
    'UserNotRegisteredException',
    'UserBlockedException',
    'DataException',
    'DatabaseException',
    'ValidationException',
    'ExternalServiceException',
    'send_user_error',
    'handle_telegram_errors',
    'handle_database_errors',
    'handle_all_errors',
    'ErrorHandler'
]