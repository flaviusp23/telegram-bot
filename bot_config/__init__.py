"""Configuration module for diabetes monitoring system"""
from .bot_constants import (
    AlertSettings,
    BotMessages,
    ButtonLabels,
    CallbackData,
    ExportSettings,
    BotSettings,
    LogMessages,
    XMLConstants,
    GraphSettings
)

# Import from main config - handle import error gracefully
try:
    from config import ADMIN_TELEGRAM_IDS
except ImportError:
    ADMIN_TELEGRAM_IDS = []

__all__ = [
    'AlertSettings',
    'BotMessages',
    'ButtonLabels',
    'CallbackData',
    'ExportSettings',
    'BotSettings',
    'LogMessages',
    'XMLConstants',
    'GraphSettings',
    'ADMIN_TELEGRAM_IDS'
]