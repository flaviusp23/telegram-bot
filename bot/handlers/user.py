"""User management handlers for the diabetes monitoring bot.

Handles:
- /status command
- /pause command
- /resume command
"""
from typing import Optional
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    log_command_usage
)
from bot.utils.error_handling import handle_database_errors
from bot.handlers.language import get_user_language, get_message
from bot_config.bot_constants import BotSettings, LogMessages
from database import db_session_context
from database.constants import UserStatusValues
from database.models import User, UserStatus

logger = logging.getLogger(__name__)


@require_registered_user
@update_last_interaction
@log_command_usage
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Check user registration status"""
    # Get user's language preference
    lang = get_user_language(context, user)
    
    # Determine alert status message
    if user.status.value == UserStatusValues.ACTIVE:
        alert_status = get_message('ALERT_STATUS_ACTIVE', lang)
    elif user.status.value == UserStatusValues.INACTIVE:
        alert_status = get_message('ALERT_STATUS_INACTIVE', lang)
    else:  # blocked
        alert_status = get_message('ALERT_STATUS_BLOCKED', lang)
    
    # Get last interaction text
    never_interacted = get_message('NEVER_INTERACTED', lang)
    
    status_text = get_message('STATUS_TEMPLATE', lang,
        first_name=user.first_name,
        family_name=user.family_name,
        alert_status=alert_status,
        registration_date=user.registration_date.strftime(BotSettings.DATETIME_FORMAT),
        last_interaction=user.last_interaction.strftime(BotSettings.DATETIME_FORMAT) if user.last_interaction else never_interacted
    )
    await update.message.reply_text(status_text)


@require_registered_user
@update_last_interaction
@log_command_usage
@handle_database_errors()
async def pause_alerts(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    user: User
) -> None:
    """Pause automatic questionnaires for user.
    
    Args:
        update: Telegram update object
        context: Bot context
        user: Registered user object
    """
    # Get user's language preference
    lang = get_user_language(context, user)
    
    with db_session_context() as db:
        # Update status to inactive
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            if db_user.status == UserStatus.inactive:
                await update.message.reply_text(get_message('PAUSE_ALREADY_PAUSED', lang))
            else:
                db_user.status = UserStatus.inactive
                await update.message.reply_text(get_message('PAUSE_SUCCESS', lang))


@require_registered_user
@update_last_interaction
@log_command_usage
@handle_database_errors()
async def resume_alerts(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    user: User
) -> None:
    """Resume automatic questionnaires for user.
    
    Args:
        update: Telegram update object
        context: Bot context
        user: Registered user object
    """
    # Get user's language preference
    lang = get_user_language(context, user)
    
    with db_session_context() as db:
        # Update status to active
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            if db_user.status == UserStatus.active:
                await update.message.reply_text(get_message('RESUME_ALREADY_ACTIVE', lang))
            elif db_user.status == UserStatus.blocked:
                await update.message.reply_text(get_message('RESUME_BLOCKED', lang))
            else:
                db_user.status = UserStatus.active
                await update.message.reply_text(get_message('RESUME_SUCCESS', lang))