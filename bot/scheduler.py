"""Scheduler functions for the diabetes monitoring bot.

Handles scheduled questionnaire sending to active users.
"""
from typing import Any, List, Tuple
import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, BadRequest

from bot.handlers.questionnaire_dds2 import send_scheduled_dds2
from bot.utils.common import handle_blocked_user
from bot_config.bot_constants import (
    BotMessages, CallbackData, LogMessages, ButtonLabels, AlertSettings
)
from database import get_active_users, db_session_context
from database.models import User, UserStatus

logger = logging.getLogger(__name__)


async def send_questionnaire_to_user(bot: Any, user: User) -> bool:
    """Send DDS-2 questionnaire to a single user.
    
    Args:
        bot: Telegram bot instance
        user: User to send questionnaire to
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        await send_scheduled_dds2(bot, user)
        return True
        
    except Forbidden:
        logger.warning(
            LogMessages.USER_BLOCKED_BOT.format(
                first_name=user.first_name, 
                telegram_id=user.telegram_id
            )
        )
        await handle_blocked_user(user)
        return False
        
    except BadRequest as e:
        logger.error(
            LogMessages.ERROR_BAD_REQUEST.format(
                telegram_id=user.telegram_id, 
                error=e
            )
        )
        return False
        
    except Exception as e:
        logger.error(
            LogMessages.ERROR_SEND_USER.format(
                telegram_id=user.telegram_id, 
                error=e
            )
        )
        return False


async def _get_active_users_for_alerts() -> List[User]:
    """Get list of active users for sending alerts.
    
    Returns:
        List of active users
    """
    with db_session_context(commit=False) as db:
        return get_active_users(db)


async def _send_alerts_to_users(bot: Any, users: List[User]) -> Tuple[int, int]:
    """Send alerts to a list of users.
    
    Args:
        bot: Telegram bot instance
        users: List of users to send alerts to
        
    Returns:
        Tuple of (sent_count, failed_count)
    """
    sent_count = 0
    failed_count = 0
    
    for user in users:
        success = await send_questionnaire_to_user(bot, user)
        if success:
            sent_count += 1
        else:
            failed_count += 1
        
        # Small delay between messages to avoid rate limits
        await asyncio.sleep(AlertSettings.MESSAGE_DELAY_SECONDS)
    
    return sent_count, failed_count


async def send_scheduled_alerts(bot: Any) -> None:
    """Send alerts to all active users.
    
    Args:
        bot: Telegram bot instance
    """
    logger.info(LogMessages.ALERT_JOB_START)
    
    try:
        # Get active users
        active_users = await _get_active_users_for_alerts()
        logger.info(
            LogMessages.ALERT_JOB_FOUND_USERS.format(count=len(active_users))
        )
        
        if not active_users:
            logger.info(LogMessages.ALERT_JOB_NO_USERS)
            return
        
        # Send alerts and collect statistics
        sent_count, failed_count = await _send_alerts_to_users(bot, active_users)
        
        logger.info(
            LogMessages.ALERT_JOB_COMPLETE.format(
                sent=sent_count, 
                failed=failed_count
            )
        )
        
    except Exception as e:
        logger.error(LogMessages.ERROR_SCHEDULED_ALERT.format(error=e))