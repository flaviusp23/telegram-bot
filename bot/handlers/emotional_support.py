"""Emotional support handler using LLaMA 3.2

Provides AI-powered emotional support for users with diabetes distress.
"""
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, ApplicationHandlerStop

from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    log_command_usage
)
from bot.llm_service import get_llm_service
from bot_config.bot_constants import BotMessages
from bot_config.llm_constants import (
    ConversationStates, SupportMessages, LLMSettings
)
from bot.handlers.language import get_user_language, get_message
from database import (
    db_session_context,
    create_assistant_interaction,
    get_user_by_telegram_id
)
from database.models import User

logger = logging.getLogger(__name__)

# Conversation states
CHATTING = ConversationStates.CHATTING

# Initialize LLM service (Google Gemini)
llm_service = get_llm_service()


@require_registered_user
@update_last_interaction
@log_command_usage
async def start_support(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> int:
    """Start emotional support conversation"""
    # Get user's latest DDS-2 score from context or database
    # Default to moderate distress (score of 6)
    default_score = (LLMSettings.MIN_DDS2_SCORE + LLMSettings.MAX_DDS2_SCORE) // 2
    dds2_score = context.user_data.get('dds2_total_score', default_score)
    distress_level = context.user_data.get('dds2_distress_level', 'moderate')
    
    # Store context for the conversation
    context.user_data['support_context'] = {
        'dds2_score': dds2_score,
        'distress_level': distress_level,
        'language': 'en',  # Could get from user preferences later
        'user_id': user.id,
        'conversation_history': []
    }
    
    # Send initial message based on distress level
    lang = context.user_data.get('language', 'en')
    initial_message = SupportMessages.INITIAL_PROMPTS.get(distress_level, {}).get(lang, "")
    if not initial_message:
        initial_message = SupportMessages.INITIAL_PROMPTS['moderate']['en']
    await update.message.reply_text(initial_message)
    
    # Instructions
    lang = get_user_language(context, user)
    instructions = get_message('CHAT_INSTRUCTIONS', lang)
    await update.message.reply_text(instructions)
    
    return CHATTING


async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle messages during support conversation"""
    user_message = update.message.text
    support_context = context.user_data.get('support_context', {})
    
    # Get user from database
    telegram_id = str(update.effective_user.id)
    with db_session_context(commit=False) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            await update.message.reply_text(BotMessages.NOT_REGISTERED)
            return ConversationHandler.END
    
    # Check if user wants to end
    if user_message.lower() in SupportMessages.END_KEYWORDS:
        return await end_support(update, context)
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Get response from LLaMA
        user_name = user.first_name if user else "there"
        
        # Get language preference
        from bot_config.languages import Languages
        lang_code = context.user_data.get('language', 'en')
        language_name = Languages.NAMES.get(lang_code, 'English')
        
        logger.info(f"Requesting AI response for user {telegram_id}")
        
        ai_response = await llm_service.generate_response(
            user_message,
            support_context.get('conversation_history', []),
            user_name,
            language_name
        )
        
        # Check if we got a valid response or a fallback
        if ai_response in [SupportMessages.SERVICE_UNAVAILABLE, SupportMessages.UNDERSTANDING_RESPONSE]:
            logger.warning(f"Gemini returned fallback response: {ai_response[:50]}...")
            # Still send the fallback message to user instead of hanging
            await update.message.reply_text(ai_response)
            
            # Optionally suggest trying again
            await update.message.reply_text(
                "💡 *Tip:* The AI service might be temporarily busy. "
                "You can try sending your message again, or type /done to end the chat.",
                parse_mode='Markdown'
            )
            return CHATTING
        
        # Save to conversation history
        support_context['conversation_history'].append({
            'role': 'user',
            'content': user_message
        })
        support_context['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response
        })
        
        # Save to database
        with db_session_context() as db:
            create_assistant_interaction(
                db=db,
                user_id=support_context['user_id'],
                prompt=user_message,
                response=ai_response
            )
        
        # Send response
        await update.message.reply_text(ai_response)
        
        # After N exchanges, gently remind about /done
        if len(support_context['conversation_history']) >= LLMSettings.REMINDER_AFTER_EXCHANGES:
            await update.message.reply_text(
                SupportMessages.DONE_REMINDER,
                parse_mode='Markdown'
            )
        
        return CHATTING
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout in support conversation for user {telegram_id}")
        await update.message.reply_text(
            "⏱️ The response is taking longer than expected. "
            "Please try again or type /done to end the chat."
        )
        return CHATTING
        
    except Exception as e:
        logger.error(f"Error in support conversation: {type(e).__name__}: {str(e)}")
        # Send a helpful message instead of generic error
        await update.message.reply_text(
            "I'm having trouble connecting to the AI service right now. "
            "Here's what you can do:\n\n"
            "• Try sending your message again\n"
            "• Type /done to end this chat\n"
            "• Come back later when the service is restored\n\n"
            "Remember, you're doing great managing your diabetes! 💪"
        )
        return CHATTING


async def end_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the support conversation with /done"""
    support_context = context.user_data.get('support_context', {})
    exchanges = len(support_context.get('conversation_history', [])) // 2
    
    # Thank you message
    await update.message.reply_text(SupportMessages.CONVERSATION_END_MESSAGE)
    
    # Log conversation stats
    logger.info(f"Support conversation ended with /done. User had {exchanges} exchanges.")
    
    # Clear conversation data
    context.user_data.pop('support_context', None)
    
    return ConversationHandler.END


async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel support conversation"""
    lang = get_user_language(context, None)
    await update.message.reply_text(
        get_message('CONVERSATION_CANCELLED', lang)
    )
    context.user_data.pop('support_context', None)
    return ConversationHandler.END


async def command_during_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle when user types a command during support conversation"""
    command = update.message.text if update.message else "/unknown"
    
    logger.info(f"Command intercepted during support: {command}")
    
    # Store the command for later use
    context.user_data['pending_command'] = command
    
    # Ask user if they want to end the conversation
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, end chat", callback_data="confirm_end_support"),
            InlineKeyboardButton("❌ No, continue", callback_data="continue_support")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"You typed `{command}` during our support chat.\n\n"
        "Do you want to end the support conversation and run this command?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Stop other handlers from processing this update
    raise ApplicationHandlerStop(CHATTING)


# Quick support after DDS-2 high score
async def offer_support_after_dds2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Offer support after high DDS-2 score"""
    # Get user for language preference
    telegram_id = str(update.effective_user.id)
    with db_session_context(commit=False) as db:
        user = get_user_by_telegram_id(db, telegram_id)
    
    lang = get_user_language(context, user)
    
    # Get distress level from context
    distress_level = context.user_data.get('dds2_distress_level', 'moderate')
    
    # Select appropriate support offer message based on distress level
    if distress_level == 'high':
        message_key = 'SUPPORT_OFFER_HIGH'
    elif distress_level == 'moderate':
        message_key = 'SUPPORT_OFFER_MODERATE'
    else:
        message_key = 'SUPPORT_OFFER_LOW'
    
    keyboard = [
        [
            InlineKeyboardButton(get_message('SUPPORT_BUTTON_YES', lang), callback_data="start_support"),
            InlineKeyboardButton(get_message('SUPPORT_BUTTON_NO', lang), callback_data="decline_support")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        get_message(message_key, lang),
        reply_markup=reply_markup
    )


async def command_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation for ending support to run a command"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_end_support":
        # User wants to end the conversation
        pending_command = context.user_data.get('pending_command', '')
        support_context = context.user_data.get('support_context', {})
        exchanges = len(support_context.get('conversation_history', [])) // 2
        
        # Clear conversation data
        context.user_data.pop('support_context', None)
        context.user_data.pop('pending_command', None)
        
        # Edit the confirmation message
        await query.edit_message_text(
            f"✅ Support chat ended after {exchanges} exchanges.\n\n"
            f"Thank you for sharing with me today. 💙\n\n"
            f"Please type {pending_command} again to run it."
        )
        
        logger.info(f"Support ended by user confirmation to run command: {pending_command}")
        return ConversationHandler.END
        
    elif query.data == "continue_support":
        # User wants to continue the conversation
        context.user_data.pop('pending_command', None)
        
        await query.edit_message_text(
            "Let's continue our conversation. 💬\n"
            "What would you like to talk about?"
        )
        return CHATTING
    
    return CHATTING


async def support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle support offer callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_support":
        # Get user
        telegram_id = str(query.from_user.id)
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            if user:
                # Get user's latest DDS-2 score from context or database
                default_score = (LLMSettings.MIN_DDS2_SCORE + LLMSettings.MAX_DDS2_SCORE) // 2
                dds2_score = context.user_data.get('dds2_total_score', default_score)
                distress_level = context.user_data.get('dds2_distress_level', 'moderate')
                
                # Store context for the conversation
                context.user_data['support_context'] = {
                    'dds2_score': dds2_score,
                    'distress_level': distress_level,
                    'language': 'en',
                    'user_id': user.id,
                    'conversation_history': []
                }
                
                # Edit the message to show we're starting
                lang = get_user_language(context, user)
                await query.edit_message_text(get_message('STARTING_SUPPORT_CHAT', lang))
                
                # Send initial message based on distress level
                lang = context.user_data.get('language', 'en')
                initial_message = SupportMessages.INITIAL_PROMPTS.get(distress_level, {}).get(lang, "")
                if not initial_message:
                    initial_message = SupportMessages.INITIAL_PROMPTS['moderate']['en']
                
                await query.message.reply_text(initial_message)
                
                # Send chat instructions in user's language
                instructions = get_message('CHAT_INSTRUCTIONS', lang)
                await query.message.reply_text(instructions)
                
                # Return CHATTING state to enter conversation
                return CHATTING
            else:
                lang = get_user_language(context, None)
                await query.edit_message_text(get_message('NOT_REGISTERED', lang))
                return ConversationHandler.END
    
    elif query.data == "decline_support":
        # Get user for language preference
        telegram_id = str(query.from_user.id)
        with db_session_context(commit=False) as db:
            user = get_user_by_telegram_id(db, telegram_id)
        lang = get_user_language(context, user)
        
        await query.edit_message_text(get_message('SUPPORT_DECLINED', lang))
        return ConversationHandler.END
    
    return ConversationHandler.END