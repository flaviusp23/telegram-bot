"""Scheduler functions for the diabetes monitoring bot.

Handles scheduled questionnaire sending to active users.
"""
import logging
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, BadRequest

from database import get_active_users, db_session_context
from database.models import User, UserStatus
from bot_config.bot_constants import (
    AlertSettings, BotMessages, ButtonLabels, 
    CallbackData, LogMessages
)

logger = logging.getLogger(__name__)


async def send_questionnaire_to_user(bot, user: User) -> bool:
    """Send questionnaire to a single user"""
    try:
        # Create the questionnaire keyboard
        keyboard = [
            [
                InlineKeyboardButton(ButtonLabels.YES, callback_data=CallbackData.DISTRESS_YES),
                InlineKeyboardButton(ButtonLabels.NO, callback_data=CallbackData.DISTRESS_NO)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Personalized message
        message = BotMessages.SCHEDULED_QUESTIONNAIRE_START.format(first_name=user.first_name)
        
        # Send message
        await bot.send_message(
            chat_id=int(user.telegram_id),
            text=message,
            reply_markup=reply_markup
        )
        
        logger.info(LogMessages.QUESTIONNAIRE_SENT.format(first_name=user.first_name, telegram_id=user.telegram_id))
        return True
        
    except Forbidden:
        # User blocked the bot
        logger.warning(LogMessages.USER_BLOCKED_BOT.format(first_name=user.first_name, telegram_id=user.telegram_id))
        # Update user status to blocked
        with db_session_context() as db:
            user = db.query(User).filter(User.id == user.id).first()
            if user:
                user.status = UserStatus.blocked
                logger.info(LogMessages.USER_STATUS_UPDATED.format(telegram_id=user.telegram_id))
        return False
        
    except BadRequest as e:
        # Invalid telegram_id or other bad request
        logger.error(LogMessages.ERROR_BAD_REQUEST.format(telegram_id=user.telegram_id, error=e))
        return False
        
    except Exception as e:
        logger.error(LogMessages.ERROR_SEND_USER.format(telegram_id=user.telegram_id, error=e))
        return False


async def send_scheduled_alerts(bot):
    """Send alerts to all active users"""
    logger.info(LogMessages.ALERT_JOB_START)
    
    try:
        with db_session_context(commit=False) as db:
            # Get all active users
            active_users = get_active_users(db)
            logger.info(LogMessages.ALERT_JOB_FOUND_USERS.format(count=len(active_users)))
            
            if not active_users:
                logger.info(LogMessages.ALERT_JOB_NO_USERS)
                return
            
            # Statistics
            sent_count = 0
            failed_count = 0
            
            # Send to each user
            for user in active_users:
                success = await send_questionnaire_to_user(bot, user)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Small delay between messages to avoid rate limits
                await asyncio.sleep(AlertSettings.MESSAGE_DELAY_SECONDS)
            
            logger.info(
                LogMessages.ALERT_JOB_COMPLETE.format(sent=sent_count, failed=failed_count)
            )
        
    except Exception as e:
        logger.error(LogMessages.ERROR_SCHEDULED_ALERT.format(error=e))