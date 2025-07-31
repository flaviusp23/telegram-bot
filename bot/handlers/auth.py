"""Authentication and registration handlers for the diabetes monitoring bot.

Handles:
- /start command
- /register command
"""
from typing import Optional
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.decorators import (
    with_user_context,
    log_command_usage,
    update_last_interaction
)
from bot.utils.error_handling import handle_all_errors
from bot.handlers.language import get_user_language, get_message
from bot_config.bot_constants import LogMessages
from bot_config.languages import Languages
from database import (
    db_session_context,
    get_user_by_telegram_id,
    create_user
)
from database.constants import DefaultValues
from database.models import User

logger = logging.getLogger(__name__)


def map_telegram_language_code(telegram_lang_code: str) -> str:
    """Map Telegram's language code to our supported languages.
    
    Args:
        telegram_lang_code: Language code from Telegram (e.g., 'en', 'es', 'ro')
        
    Returns:
        Supported language code or English as default
    """
    if not telegram_lang_code:
        return Languages.ENGLISH
    
    # Extract the base language code (first 2 characters)
    base_lang = telegram_lang_code[:2].lower()
    
    # Map to our supported languages
    if base_lang in Languages.SUPPORTED:
        return base_lang
    
    # Default to English
    return Languages.ENGLISH


@with_user_context
@log_command_usage
@handle_all_errors()
async def start(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    user: Optional[User] = None
) -> None:
    """Send a message when the command /start is issued.
    
    Args:
        update: Telegram update object
        context: Bot context
        user: User object if registered, None otherwise
    """
    telegram_user = update.effective_user
    
    if user:
        # User is already registered
        lang = get_user_language(context, user)
        await update.message.reply_text(
            get_message('WELCOME_BACK', lang, first_name=user.first_name)
        )
    else:
        # New user - detect language from Telegram
        detected_lang = map_telegram_language_code(telegram_user.language_code)
        
        # Store detected language in context temporarily
        context.user_data['detected_language'] = detected_lang
        context.user_data['language'] = detected_lang
        
        # Create language selection buttons
        keyboard = []
        for lang_code in Languages.SUPPORTED:
            flag = Languages.FLAGS[lang_code]
            name = Languages.NAMES[lang_code]
            # Mark detected language
            if lang_code == detected_lang:
                button_text = f"✓ {flag} {name}"
            else:
                button_text = f"{flag} {name}"
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"initial_language_{lang_code}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send welcome message with language selection
        welcome_text = get_message('WELCOME_NEW', detected_lang, first_name=telegram_user.first_name)
        language_prompt = get_message('LANGUAGE_SELECTION', detected_lang)
        
        await update.message.reply_text(
            f"{welcome_text}\n\n{language_prompt}",
            reply_markup=reply_markup
        )


@with_user_context
@log_command_usage
@handle_all_errors()
async def register(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    user: Optional[User] = None
) -> None:
    """Register a new user.
    
    Args:
        update: Telegram update object
        context: Bot context
        user: User object if already registered, None otherwise
    """
    telegram_user = update.effective_user
    telegram_id = str(telegram_user.id)
    
    # Get user's language preference
    lang = get_user_language(context, user)
    
    # Check if already registered
    if user:
        await update.message.reply_text(
            get_message('ALREADY_REGISTERED', lang, first_name=user.first_name)
        )
        return
    
    # Register new user
    try:
        with db_session_context() as db:
            user = create_user(
                db=db,
                first_name=telegram_user.first_name or DefaultValues.DEFAULT_NAME,
                family_name=telegram_user.last_name or DefaultValues.DEFAULT_FAMILY_NAME,
                passport_id=None,
                phone_number=None,
                telegram_id=telegram_id,
                email=None
            )
            
            # Update user's language preference if set in context
            if 'language' in context.user_data and context.user_data['language'] != Languages.ENGLISH:
                user.language = context.user_data['language']
                db.commit()
            
            await update.message.reply_text(
                get_message('REGISTRATION_SUCCESS', lang, first_name=user.first_name)
            )
    except Exception as e:
        logger.error(f"Registration error for user {telegram_id}: {str(e)}")
        await update.message.reply_text(
            get_message('REGISTRATION_ERROR', lang)
        )


async def initial_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle initial language selection for new users"""
    query = update.callback_query
    await query.answer()
    
    # Extract language code from callback data
    if query.data.startswith("initial_language_"):
        new_lang = query.data.replace("initial_language_", "")
        
        if new_lang in Languages.SUPPORTED:
            # Update context with selected language
            context.user_data['language'] = new_lang
            
            # Send confirmation and registration prompt in selected language
            confirmation = get_message('LANGUAGE_CHANGED', new_lang)
            register_prompt = get_message('REGISTER_PROMPT', new_lang)
            
            await query.edit_message_text(
                f"{confirmation}\n\n{register_prompt}"
            )
            
            logger.info(f"New user selected language: {new_lang}")