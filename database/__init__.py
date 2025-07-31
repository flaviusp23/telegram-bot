"""Database package for diabetes monitoring system"""

# Import commonly used items for easier access
from database.constants import (
    UserStatusValues, QuestionTypes, ResponseValues,
    DatabaseSettings, FieldLengths, DefaultValues, TableNames
)
from database.database import get_db, SessionLocal, engine, Base
from database.helpers import (
    create_user, get_user_by_telegram_id, get_active_users,
    update_last_interaction, create_response, get_user_responses,
    create_assistant_interaction, get_user_interactions
)
from database.models import User, Response, AssistantInteraction, UserStatus
from database.session_utils import (
    db_session_context,
    with_db_session,
    get_db_for_request
)

__all__ = [
    # Database
    'get_db', 'SessionLocal', 'engine', 'Base',
    # Models
    'User', 'Response', 'AssistantInteraction', 'UserStatus',
    # Helpers
    'create_user', 'get_user_by_telegram_id', 'get_active_users',
    'update_last_interaction', 'create_response', 'get_user_responses',
    'create_assistant_interaction', 'get_user_interactions',
    # Constants
    'UserStatusValues', 'QuestionTypes', 'ResponseValues',
    'DatabaseSettings', 'FieldLengths', 'DefaultValues', 'TableNames',
    # Session utilities
    'db_session_context', 'with_db_session', 'get_db_for_request'
]