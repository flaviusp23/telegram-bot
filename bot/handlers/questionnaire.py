"""Questionnaire handlers for the diabetes monitoring bot.

Handles:
- /questionnaire command
- Button callbacks for distress check and severity rating
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import (
    get_user_by_telegram_id,
    create_response,
    db_session_context
)
from database.models import User
from database.constants import QuestionTypes, ResponseValues
from bot_config.bot_constants import BotMessages, ButtonLabels, CallbackData, LogMessages
from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    log_command_usage
)

logger = logging.getLogger(__name__)


@require_registered_user
@update_last_interaction
@log_command_usage
async def questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Start the questionnaire with inline buttons"""
    # Store user_id in context for callback
    context.user_data['user_id'] = user.id
    context.user_data['user_first_name'] = user.first_name
    
    # First question: Yes/No distress check
    keyboard = [
        [
            InlineKeyboardButton(ButtonLabels.YES, callback_data=CallbackData.DISTRESS_YES),
            InlineKeyboardButton(ButtonLabels.NO, callback_data=CallbackData.DISTRESS_NO)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        BotMessages.QUESTIONNAIRE_START.format(user_name=user.first_name),
        reply_markup=reply_markup
    )


def get_user_from_context_or_lookup(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Helper function to get user ID from context or database lookup.
    
    Args:
        query: The callback query object
        context: The telegram context
        
    Returns:
        tuple: (user_id, error_occurred) - user_id is None if error occurred
    """
    user_id = context.user_data.get('user_id')
    
    # If no user_id in context (scheduled message), get from telegram_id
    if not user_id:
        telegram_id = str(query.from_user.id)
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            if user:
                user_id = user.id
                context.user_data['user_id'] = user_id
                return user_id, False
            else:
                return None, True
    
    return user_id, False


async def handle_distress_response(query, context: ContextTypes.DEFAULT_TYPE, response_value: str) -> None:
    """
    Handle distress check response (yes/no).
    
    Args:
        query: The callback query object
        context: The telegram context
        response_value: The response value (YES or NO)
    """
    # Get user ID
    user_id, error = get_user_from_context_or_lookup(query, context)
    if error:
        await query.edit_message_text(BotMessages.ERROR_USER_NOT_FOUND)
        return
    
    # Record the response
    try:
        with db_session_context() as db:
            create_response(
                db=db,
                user_id=user_id,
                question_type=QuestionTypes.DISTRESS_CHECK,
                response_value=response_value
            )
    except Exception as e:
        logger.error(LogMessages.ERROR_RECORDING_RESPONSE.format(error=e))
        await query.edit_message_text(BotMessages.ERROR_RECORDING_RESPONSE)
        return
    
    if response_value == ResponseValues.NO:
        # No distress, end questionnaire
        await query.edit_message_text(BotMessages.NO_DISTRESS_RESPONSE)
        context.user_data.clear()
    else:
        # Yes to distress, ask severity
        keyboard = [
            [
                InlineKeyboardButton(ButtonLabels.SEVERITY_1, callback_data=CallbackData.severity(1)),
                InlineKeyboardButton(ButtonLabels.SEVERITY_2, callback_data=CallbackData.severity(2))
            ],
            [
                InlineKeyboardButton(ButtonLabels.SEVERITY_3, callback_data=CallbackData.severity(3)),
                InlineKeyboardButton(ButtonLabels.SEVERITY_4, callback_data=CallbackData.severity(4))
            ],
            [
                InlineKeyboardButton(ButtonLabels.SEVERITY_5, callback_data=CallbackData.severity(5))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            BotMessages.DISTRESS_SEVERITY_QUESTION,
            reply_markup=reply_markup
        )


async def handle_severity_response(query, context: ContextTypes.DEFAULT_TYPE, severity: str) -> None:
    """
    Handle severity rating response (1-5).
    
    Args:
        query: The callback query object
        context: The telegram context
        severity: The severity rating (1-5)
    """
    # Get user ID
    user_id, error = get_user_from_context_or_lookup(query, context)
    if error:
        await query.edit_message_text(BotMessages.ERROR_USER_NOT_FOUND)
        return
    
    # Record the severity
    try:
        with db_session_context() as db:
            create_response(
                db=db,
                user_id=user_id,
                question_type=QuestionTypes.SEVERITY_RATING,
                response_value=severity
            )
    except Exception as e:
        logger.error(f"Error recording severity: {e}")
        await query.edit_message_text(BotMessages.ERROR_RECORDING_RESPONSE)
        return
    
    # Provide appropriate response based on severity
    severity_int = int(severity)
    if severity_int in ResponseValues.MILD_SEVERITY_RANGE:
        message = BotMessages.SEVERITY_MILD_RESPONSE
    elif severity_int in ResponseValues.MODERATE_SEVERITY_RANGE:
        message = BotMessages.SEVERITY_MODERATE_RESPONSE
    else:  # High severity (4 or 5)
        message = BotMessages.SEVERITY_HIGH_RESPONSE
    
    await query.edit_message_text(message)
    context.user_data.clear()


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main button callback dispatcher.
    
    Determines the type of callback and routes to appropriate handler.
    """
    query = update.callback_query
    await query.answer()
    
    # Determine callback type and dispatch to appropriate handler
    if query.data in [CallbackData.DISTRESS_YES, CallbackData.DISTRESS_NO]:
        # Handle distress check response
        response_value = ResponseValues.YES if query.data == CallbackData.DISTRESS_YES else ResponseValues.NO
        await handle_distress_response(query, context, response_value)
    
    elif query.data.startswith(CallbackData.SEVERITY_PREFIX):
        # Handle severity rating
        severity = query.data.split("_")[1]
        await handle_severity_response(query, context, severity)
    
    else:
        # Unknown callback data
        logger.warning(f"Unknown callback data received: {query.data}")
        await query.edit_message_text(BotMessages.ERROR_GENERIC)