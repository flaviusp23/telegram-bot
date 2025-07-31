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
from bot_config.bot_constants import BotMessages, BotSettings, LogMessages
from database import db_session_context
from database.constants import UserStatusValues
from database.models import User, UserStatus

logger = logging.getLogger(__name__)


@require_registered_user
@update_last_interaction
@log_command_usage
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Check user registration status"""
    # Determine alert status message
    if user.status.value == UserStatusValues.ACTIVE:
        alert_status = BotMessages.ALERT_STATUS_ACTIVE
    elif user.status.value == UserStatusValues.INACTIVE:
        alert_status = BotMessages.ALERT_STATUS_INACTIVE
    else:  # blocked
        alert_status = BotMessages.ALERT_STATUS_BLOCKED
    
    status_text = BotMessages.STATUS_TEMPLATE.format(
        first_name=user.first_name,
        family_name=user.family_name,
        alert_status=alert_status,
        registration_date=user.registration_date.strftime(BotSettings.DATETIME_FORMAT),
        last_interaction=user.last_interaction.strftime(BotSettings.DATETIME_FORMAT) if user.last_interaction else 'Never'
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
    with db_session_context() as db:
        # Update status to inactive
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            if db_user.status == UserStatus.inactive:
                await update.message.reply_text(BotMessages.PAUSE_ALREADY_PAUSED)
            else:
                db_user.status = UserStatus.inactive
                await update.message.reply_text(BotMessages.PAUSE_SUCCESS)


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
    with db_session_context() as db:
        # Update status to active
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            if db_user.status == UserStatus.active:
                await update.message.reply_text(BotMessages.RESUME_ALREADY_ACTIVE)
            elif db_user.status == UserStatus.blocked:
                await update.message.reply_text(BotMessages.RESUME_BLOCKED)
            else:
                db_user.status = UserStatus.active
                await update.message.reply_text(BotMessages.RESUME_SUCCESS)