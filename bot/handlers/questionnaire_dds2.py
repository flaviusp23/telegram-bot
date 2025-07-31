"""DDS-2 Questionnaire handlers for the diabetes monitoring bot.

Implements the 2-item Diabetes Distress Scale (DDS-2) with:
- Question 1: Feeling overwhelmed by the demands of living with diabetes
- Question 2: Feeling that I am often failing with my diabetes regimen
- 6-point scale: 1 (not a problem) to 6 (very serious problem)
"""
from typing import Optional, Dict, Any
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    log_command_usage
)
from bot.utils.common import (
    send_error_message,
    with_error_handling,
    validate_user_context
)
from bot_config.bot_constants import BotMessages, ButtonLabels, CallbackData
from database import (
    db_session_context,
    create_response,
    get_user_by_telegram_id
)
from database.constants import QuestionTypes, ResponseValues
from database.models import User

logger = logging.getLogger(__name__)


@require_registered_user
@update_last_interaction
@log_command_usage
async def questionnaire_dds2(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Start the DDS-2 questionnaire"""
    # Store user info in context for callbacks
    context.user_data['user_id'] = user.id
    context.user_data['user_first_name'] = user.first_name
    context.user_data['dds2_mode'] = True
    context.user_data['dds2_responses'] = {}
    
    # Send intro message
    await update.message.reply_text(
        BotMessages.DDS2_INTRO.format(user_name=user.first_name)
    )
    
    # Send first question
    await send_dds2_question_1(update.message, context)


def _create_dds2_keyboard(question_num: int) -> InlineKeyboardMarkup:
    """Create DDS-2 scale keyboard for a question.
    
    Args:
        question_num: Question number (1 or 2)
        
    Returns:
        InlineKeyboardMarkup with 6-point scale buttons
    """
    callback_func = CallbackData.dds2_q1 if question_num == 1 else CallbackData.dds2_q2
    buttons = [
        (ButtonLabels.DDS2_1, callback_func(1)),
        (ButtonLabels.DDS2_2, callback_func(2)),
        (ButtonLabels.DDS2_3, callback_func(3)),
        (ButtonLabels.DDS2_4, callback_func(4)),
        (ButtonLabels.DDS2_5, callback_func(5)),
        (ButtonLabels.DDS2_6, callback_func(6))
    ]
    
    keyboard = [
        [InlineKeyboardButton(text, callback_data=data) for text, data in buttons[:3]],
        [InlineKeyboardButton(text, callback_data=data) for text, data in buttons[3:]]
    ]
    
    return InlineKeyboardMarkup(keyboard)


async def send_dds2_question_1(message: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send DDS-2 Question 1 with 6-point scale buttons.
    
    Args:
        message: Telegram message object
        context: Bot context
    """
    reply_markup = _create_dds2_keyboard(1)
    await message.reply_text(
        BotMessages.DDS2_Q1_OVERWHELMED,
        reply_markup=reply_markup
    )


async def _get_or_validate_user_id(query: Any, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """Get user ID from context or database.
    
    Args:
        query: Telegram callback query
        context: Bot context
        
    Returns:
        User ID if found, None otherwise
    """
    user_id = validate_user_context(context)
    if not user_id:
        telegram_id = str(query.from_user.id)
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            if user:
                user_id = user.id
                context.user_data['user_id'] = user_id
            else:
                await send_error_message(query, BotMessages.ERROR_USER_NOT_FOUND)
                return None
    return user_id


async def _record_dds2_response(
    user_id: int, 
    question_type: str, 
    rating: int
) -> bool:
    """Record a DDS-2 response in the database.
    
    Args:
        user_id: User ID
        question_type: Question type constant
        rating: Response rating (1-6)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_session_context() as db:
            create_response(
                db=db,
                user_id=user_id,
                question_type=question_type,
                response_value=str(rating)
            )
        return True
    except Exception as e:
        logger.error(f"Error recording DDS-2 response: {e}")
        return False


@with_error_handling(error_message=BotMessages.ERROR_RECORDING_RESPONSE)
async def handle_dds2_q1_response(
    query: Any, 
    context: ContextTypes.DEFAULT_TYPE, 
    rating: int
) -> None:
    """Handle DDS-2 Question 1 response and show Question 2.
    
    Args:
        query: Telegram callback query
        context: Bot context
        rating: User's rating (1-6)
    """
    # Get user ID
    user_id = await _get_or_validate_user_id(query, context)
    if not user_id:
        return
    
    # Store response in context
    context.user_data['dds2_responses']['q1'] = rating
    
    # Record Q1 response
    success = await _record_dds2_response(
        user_id, 
        QuestionTypes.DDS2_Q1_OVERWHELMED, 
        rating
    )
    if not success:
        await send_error_message(query, BotMessages.ERROR_RECORDING_RESPONSE)
        return
    
    # Send Question 2
    reply_markup = _create_dds2_keyboard(2)
    await query.edit_message_text(
        BotMessages.DDS2_Q2_FAILING,
        reply_markup=reply_markup
    )


def _calculate_dds2_scores(context: ContextTypes.DEFAULT_TYPE, q2_rating: int) -> Dict[str, Any]:
    """Calculate DDS-2 total score and distress level.
    
    Args:
        context: Bot context with Q1 response
        q2_rating: Q2 rating
        
    Returns:
        Dict with total_score and distress_level
    """
    q1_score = context.user_data['dds2_responses'].get('q1', 1)
    total_score = q1_score + q2_rating
    distress_level = ResponseValues.calculate_dds2_distress_level(total_score)
    
    return {
        'total_score': total_score,
        'distress_level': distress_level,
        'q1_score': q1_score,
        'q2_score': q2_rating
    }


async def _send_distress_level_response(
    query: Any, 
    distress_level: str
) -> None:
    """Send appropriate response based on distress level.
    
    Args:
        query: Telegram callback query
        distress_level: Calculated distress level
    """
    distress_messages = {
        "low": BotMessages.DDS2_LOW_DISTRESS_RESPONSE,
        "moderate": BotMessages.DDS2_MODERATE_DISTRESS_RESPONSE,
        "high": BotMessages.DDS2_HIGH_DISTRESS_RESPONSE
    }
    
    message = distress_messages.get(distress_level, BotMessages.DDS2_LOW_DISTRESS_RESPONSE)
    await query.edit_message_text(message)
    
    # Always offer AI support after questionnaire
    keyboard = [[
        InlineKeyboardButton("💬 Chat with AI Support", callback_data="start_support"),
        InlineKeyboardButton("Not now", callback_data="decline_support")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Customize message based on distress level
    if distress_level == "high":
        support_message = (
            "I noticed you're experiencing significant distress. "
            "Would you like to chat with our AI support assistant? "
            "I'm here to listen and provide emotional support."
        )
    elif distress_level == "moderate":
        support_message = (
            "It seems you're dealing with some challenges. "
            "Would you like to talk about it with our AI support assistant?"
        )
    else:  # low
        support_message = (
            "Great job managing your diabetes! "
            "Would you like to chat with our AI assistant about maintaining your positive habits?"
        )
    
    await query.message.reply_text(
        support_message,
        reply_markup=reply_markup
    )


@with_error_handling(error_message=BotMessages.ERROR_RECORDING_RESPONSE)
async def handle_dds2_q2_response(
    query: Any, 
    context: ContextTypes.DEFAULT_TYPE, 
    rating: int
) -> None:
    """Handle DDS-2 Question 2 response and calculate total score.
    
    Args:
        query: Telegram callback query
        context: Bot context
        rating: User's rating (1-6)
    """
    # Get user ID
    user_id = await _get_or_validate_user_id(query, context)
    if not user_id:
        return
    
    # Store response
    context.user_data['dds2_responses']['q2'] = rating
    
    # Record Q2 response
    success = await _record_dds2_response(
        user_id, 
        QuestionTypes.DDS2_Q2_FAILING, 
        rating
    )
    if not success:
        await send_error_message(query, BotMessages.ERROR_RECORDING_RESPONSE)
        return
    
    # Calculate scores
    scores = _calculate_dds2_scores(context, rating)
    
    # Store total score for future LLM context
    context.user_data['dds2_total_score'] = scores['total_score']
    context.user_data['dds2_distress_level'] = scores['distress_level']
    
    # Send appropriate response
    await _send_distress_level_response(query, scores['distress_level'])
    
    # Clear temporary context data (keep scores for potential LLM use)
    context.user_data.pop('dds2_responses', None)
    context.user_data.pop('dds2_mode', None)


async def button_callback_dds2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle DDS-2 button callbacks"""
    query = update.callback_query
    await query.answer()
    
    # Check if this is a DDS-2 callback
    if query.data.startswith(CallbackData.DDS2_Q1_PREFIX):
        # Handle Question 1 response
        rating = int(query.data.split("_")[-1])
        await handle_dds2_q1_response(query, context, rating)
    
    elif query.data.startswith(CallbackData.DDS2_Q2_PREFIX):
        # Handle Question 2 response
        rating = int(query.data.split("_")[-1])
        await handle_dds2_q2_response(query, context, rating)
    
    else:
        # Not a DDS-2 callback, pass to legacy handler
        return False
    
    return True


# For scheduled questionnaires, we'll use the same flow
async def send_scheduled_dds2(bot: Any, user: User) -> None:
    """Send scheduled DDS-2 questionnaire to a user.
    
    Args:
        bot: Telegram bot instance
        user: User to send questionnaire to
    """
    try:
        # Send intro message
        await bot.send_message(
            chat_id=user.telegram_id,
            text=BotMessages.DDS2_INTRO.format(user_name=user.first_name)
        )
        
        # Send first question with keyboard
        reply_markup = _create_dds2_keyboard(1)
        await bot.send_message(
            chat_id=user.telegram_id,
            text=BotMessages.DDS2_Q1_OVERWHELMED,
            reply_markup=reply_markup
        )
        
        logger.info(f"Sent scheduled DDS-2 questionnaire to {user.first_name} (ID: {user.telegram_id})")
        
    except Exception as e:
        logger.error(f"Error sending scheduled DDS-2 to {user.telegram_id}: {e}")