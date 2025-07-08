"""Database package for diabetes monitoring system"""

# Import commonly used items for easier access
from database.database import get_db, SessionLocal, engine, Base
from database.models import User, Response, AssistantInteraction, UserStatus
from database.helpers import (
    add_user,
    get_user_by_telegram_id,
    get_active_users,
    record_response,
    get_user_responses,
    record_assistant_interaction,
    get_user_interactions
)
from database.constants import (
    UserStatusValues,
    QuestionTypes,
    ResponseValues,
    DatabaseSettings,
    FieldLengths,
    DefaultValues,
    TableNames
)

__all__ = [
    # Database
    'get_db', 'SessionLocal', 'engine', 'Base',
    # Models
    'User', 'Response', 'AssistantInteraction', 'UserStatus',
    # Helpers
    'add_user', 'get_user_by_telegram_id', 'get_active_users',
    'record_response', 'get_user_responses',
    'record_assistant_interaction', 'get_user_interactions',
    # Constants
    'UserStatusValues', 'QuestionTypes', 'ResponseValues',
    'DatabaseSettings', 'FieldLengths', 'DefaultValues', 'TableNames'
]