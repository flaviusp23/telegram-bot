"""DDS-2 Questionnaire handlers for the diabetes monitoring bot.

Implements the 2-item Diabetes Distress Scale (DDS-2) with:
- Question 1: Feeling overwhelmed by the demands of living with diabetes
- Question 2: Feeling that I am often failing with my diabetes regimen
- 6-point scale: 1 (not a problem) to 6 (very serious problem)
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


async def send_dds2_question_1(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send DDS-2 Question 1 with 6-point scale buttons"""
    keyboard = [
        [
            InlineKeyboardButton(ButtonLabels.DDS2_1, callback_data=CallbackData.dds2_q1(1)),
            InlineKeyboardButton(ButtonLabels.DDS2_2, callback_data=CallbackData.dds2_q1(2)),
            InlineKeyboardButton(ButtonLabels.DDS2_3, callback_data=CallbackData.dds2_q1(3))
        ],
        [
            InlineKeyboardButton(ButtonLabels.DDS2_4, callback_data=CallbackData.dds2_q1(4)),
            InlineKeyboardButton(ButtonLabels.DDS2_5, callback_data=CallbackData.dds2_q1(5)),
            InlineKeyboardButton(ButtonLabels.DDS2_6, callback_data=CallbackData.dds2_q1(6))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        BotMessages.DDS2_Q1_OVERWHELMED,
        reply_markup=reply_markup
    )


async def handle_dds2_q1_response(query, context: ContextTypes.DEFAULT_TYPE, rating: int) -> None:
    """Handle DDS-2 Question 1 response and show Question 2"""
    # Get user ID
    user_id = context.user_data.get('user_id')
    if not user_id:
        telegram_id = str(query.from_user.id)
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            if user:
                user_id = user.id
                context.user_data['user_id'] = user_id
            else:
                await query.edit_message_text(BotMessages.ERROR_USER_NOT_FOUND)
                return
    
    # Store response in context
    context.user_data['dds2_responses']['q1'] = rating
    
    # Record Q1 response
    try:
        with db_session_context() as db:
            create_response(
                db=db,
                user_id=user_id,
                question_type=QuestionTypes.DDS2_Q1_OVERWHELMED,
                response_value=str(rating)
            )
    except Exception as e:
        logger.error(f"Error recording DDS-2 Q1 response: {e}")
        await query.edit_message_text(BotMessages.ERROR_RECORDING_RESPONSE)
        return
    
    # Send Question 2
    keyboard = [
        [
            InlineKeyboardButton(ButtonLabels.DDS2_1, callback_data=CallbackData.dds2_q2(1)),
            InlineKeyboardButton(ButtonLabels.DDS2_2, callback_data=CallbackData.dds2_q2(2)),
            InlineKeyboardButton(ButtonLabels.DDS2_3, callback_data=CallbackData.dds2_q2(3))
        ],
        [
            InlineKeyboardButton(ButtonLabels.DDS2_4, callback_data=CallbackData.dds2_q2(4)),
            InlineKeyboardButton(ButtonLabels.DDS2_5, callback_data=CallbackData.dds2_q2(5)),
            InlineKeyboardButton(ButtonLabels.DDS2_6, callback_data=CallbackData.dds2_q2(6))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        BotMessages.DDS2_Q2_FAILING,
        reply_markup=reply_markup
    )


async def handle_dds2_q2_response(query, context: ContextTypes.DEFAULT_TYPE, rating: int) -> None:
    """Handle DDS-2 Question 2 response and calculate total score"""
    # Get user ID
    user_id = context.user_data.get('user_id')
    if not user_id:
        telegram_id = str(query.from_user.id)
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            if user:
                user_id = user.id
            else:
                await query.edit_message_text(BotMessages.ERROR_USER_NOT_FOUND)
                return
    
    # Store response
    context.user_data['dds2_responses']['q2'] = rating
    
    # Record Q2 response
    try:
        with db_session_context() as db:
            create_response(
                db=db,
                user_id=user_id,
                question_type=QuestionTypes.DDS2_Q2_FAILING,
                response_value=str(rating)
            )
    except Exception as e:
        logger.error(f"Error recording DDS-2 Q2 response: {e}")
        await query.edit_message_text(BotMessages.ERROR_RECORDING_RESPONSE)
        return
    
    # Calculate total DDS-2 score
    q1_score = context.user_data['dds2_responses'].get('q1', 1)
    q2_score = rating
    total_score = q1_score + q2_score
    
    # Store total score for future LLM context
    context.user_data['dds2_total_score'] = total_score
    context.user_data['dds2_distress_level'] = ResponseValues.calculate_dds2_distress_level(total_score)
    
    # Determine response based on distress level
    distress_level = ResponseValues.calculate_dds2_distress_level(total_score)
    
    if distress_level == "low":
        message = BotMessages.DDS2_LOW_DISTRESS_RESPONSE
    elif distress_level == "moderate":
        message = BotMessages.DDS2_MODERATE_DISTRESS_RESPONSE
    else:  # high
        message = BotMessages.DDS2_HIGH_DISTRESS_RESPONSE
    
    await query.edit_message_text(message)
    
    # Clear context data (except score for potential LLM use)
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
async def send_scheduled_dds2(bot, user: User) -> None:
    """Send scheduled DDS-2 questionnaire to a user"""
    try:
        # Send intro message
        await bot.send_message(
            chat_id=user.telegram_id,
            text=BotMessages.DDS2_INTRO.format(user_name=user.first_name)
        )
        
        # Send first question
        keyboard = [
            [
                InlineKeyboardButton(ButtonLabels.DDS2_1, callback_data=CallbackData.dds2_q1(1)),
                InlineKeyboardButton(ButtonLabels.DDS2_2, callback_data=CallbackData.dds2_q1(2)),
                InlineKeyboardButton(ButtonLabels.DDS2_3, callback_data=CallbackData.dds2_q1(3))
            ],
            [
                InlineKeyboardButton(ButtonLabels.DDS2_4, callback_data=CallbackData.dds2_q1(4)),
                InlineKeyboardButton(ButtonLabels.DDS2_5, callback_data=CallbackData.dds2_q1(5)),
                InlineKeyboardButton(ButtonLabels.DDS2_6, callback_data=CallbackData.dds2_q1(6))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(
            chat_id=user.telegram_id,
            text=BotMessages.DDS2_Q1_OVERWHELMED,
            reply_markup=reply_markup
        )
        
        logger.info(f"Sent scheduled DDS-2 questionnaire to {user.first_name} (ID: {user.telegram_id})")
        
    except Exception as e:
        logger.error(f"Error sending scheduled DDS-2 to {user.telegram_id}: {e}")