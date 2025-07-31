"""Language selection handler for multi-language support"""
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.decorators import (
    require_registered_user,
    update_last_interaction,
    log_command_usage
)
from bot_config.languages import Languages, Messages
from database import db_session_context
from database.models import User

logger = logging.getLogger(__name__)


def get_user_language(context: ContextTypes.DEFAULT_TYPE, user: User = None) -> str:
    """Get user's preferred language from context or user object"""
    # First check context
    lang = context.user_data.get('language')
    if lang and lang in Languages.SUPPORTED:
        return lang
    
    # Then check user object
    if user and hasattr(user, 'language') and user.language in Languages.SUPPORTED:
        context.user_data['language'] = user.language
        return user.language
    
    # Default to English
    return Languages.ENGLISH


def get_message(message_key: str, language: str = None, **kwargs) -> str:
    """Get a message in the specified language"""
    if language not in Languages.SUPPORTED:
        language = Languages.ENGLISH
    
    messages = getattr(Messages, message_key, {})
    if isinstance(messages, dict) and language in messages:
        message = messages[language]
        if kwargs:
            return message.format(**kwargs)
        return message
    
    # Fallback to English if translation not found
    if isinstance(messages, dict) and Languages.ENGLISH in messages:
        message = messages[Languages.ENGLISH]
        if kwargs:
            return message.format(**kwargs)
        return message
    
    return f"Message {message_key} not found"


@require_registered_user
@update_last_interaction
@log_command_usage
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Handle /language command"""
    current_lang = get_user_language(context, user)
    
    # Create language selection buttons
    keyboard = []
    for lang_code in Languages.SUPPORTED:
        flag = Languages.FLAGS[lang_code]
        name = Languages.NAMES[lang_code]
        # Mark current language
        if lang_code == current_lang:
            button_text = f"✓ {flag} {name}"
        else:
            button_text = f"{flag} {name}"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"set_language_{lang_code}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message in current language
    message = get_message('LANGUAGE_SELECTION', current_lang)
    await update.message.reply_text(message, reply_markup=reply_markup)


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection callbacks"""
    query = update.callback_query
    await query.answer()
    
    # Extract language code from callback data
    if query.data.startswith("set_language_"):
        new_lang = query.data.replace("set_language_", "")
        
        if new_lang in Languages.SUPPORTED:
            # Update user's language in database
            telegram_id = str(query.from_user.id)
            with db_session_context() as db:
                user = db.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.language = new_lang
                    db.commit()
                    
                    # Update context
                    context.user_data['language'] = new_lang
                    
                    # Send confirmation in new language
                    message = get_message('LANGUAGE_CHANGED', new_lang)
                    await query.edit_message_text(message)
                    
                    logger.info(f"User {user.id} changed language to {new_lang}")
                else:
                    # Get current language from context or default
                    current_lang = get_user_language(context)
                    error_message = get_message('ERROR_USER_NOT_FOUND', current_lang)
                    await query.edit_message_text(error_message)
        else:
            # Get current language from context or default
            current_lang = get_user_language(context)
            error_message = get_message('ERROR_INVALID_LANGUAGE', current_lang)
            await query.edit_message_text(error_message)