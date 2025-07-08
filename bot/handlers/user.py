"""User management handlers for the diabetes monitoring bot.

Handles:
- /status command
- /pause command
- /resume command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db_session_context
from database.models import User, UserStatus
from database.constants import UserStatusValues
from bot_config.bot_constants import BotMessages, BotSettings, LogMessages
from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    log_command_usage
)

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
async def pause_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Pause automatic questionnaires for user"""
    try:
        with db_session_context() as db:
            # Update status to inactive
            user = db.query(User).filter(User.id == user.id).first()
            if user:
                if user.status == UserStatus.inactive:
                    await update.message.reply_text(BotMessages.PAUSE_ALREADY_PAUSED)
                else:
                    user.status = UserStatus.inactive
                    await update.message.reply_text(BotMessages.PAUSE_SUCCESS)
        
    except Exception as e:
        logger.error(LogMessages.ERROR_PAUSING_ALERTS.format(error=e))
        await update.message.reply_text(BotMessages.ERROR_GENERIC)


@require_registered_user
@update_last_interaction
@log_command_usage
async def resume_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Resume automatic questionnaires for user"""
    try:
        with db_session_context() as db:
            # Update status to active
            user = db.query(User).filter(User.id == user.id).first()
            if user:
                if user.status == UserStatus.active:
                    await update.message.reply_text(BotMessages.RESUME_ALREADY_ACTIVE)
                elif user.status == UserStatus.blocked:
                    await update.message.reply_text(BotMessages.RESUME_BLOCKED)
                else:
                    user.status = UserStatus.active
                    await update.message.reply_text(BotMessages.RESUME_SUCCESS)
        
    except Exception as e:
        logger.error(LogMessages.ERROR_RESUMING_ALERTS.format(error=e))
        await update.message.reply_text(BotMessages.ERROR_GENERIC)