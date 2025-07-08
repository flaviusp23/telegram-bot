"""Database helper functions with consistent naming conventions.

Naming conventions:
- Functions: snake_case with consistent verb prefixes:
  - create_* for creating new records
  - get_* for retrieving records
  - update_* for modifying records
  - delete_* for removing records
- Variables: snake_case
  - user (not user_obj, db_user, etc.)
  - telegram_id (not telegramId)
- Parameters: snake_case with descriptive names
"""
from sqlalchemy.orm import Session
from database.models import User, Response, AssistantInteraction, UserStatus
from database.constants import DefaultValues
from datetime import datetime

# User helper functions
def create_user(db: Session, first_name: str, family_name: str, passport_id: str, 
                phone_number: str, telegram_id: str, email: str) -> User:
    """Create new user in database"""
    user = User(
        first_name=first_name,
        family_name=family_name,
        passport_id=passport_id,
        phone_number=phone_number,
        telegram_id=telegram_id,
        email=email
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_telegram_id(db: Session, telegram_id: str) -> User:
    """Get user by telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_active_users(db: Session) -> list[User]:
    """Get all active users for sending alerts"""
    return db.query(User).filter(User.status == UserStatus.active).all()

def update_last_interaction(db: Session, user_id: int):
    """Update user's last interaction timestamp"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_interaction = datetime.now()
        db.commit()

# Response helper functions
def create_response(db: Session, user_id: int, question_type: str, response_value: str) -> Response:
    """Create questionnaire response in database"""
    response = Response(
        user_id=user_id,
        question_type=question_type,
        response_value=response_value
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    
    # Update last interaction
    update_last_interaction(db, user_id)
    
    return response

def get_user_responses(db: Session, user_id: int, start_date: datetime, end_date: datetime) -> list[Response]:
    """Get user responses within date range"""
    return db.query(Response).filter(
        Response.user_id == user_id,
        Response.response_timestamp >= start_date,
        Response.response_timestamp <= end_date
    ).order_by(Response.response_timestamp.desc()).all()

# Assistant interaction helper functions
def create_assistant_interaction(db: Session, user_id: int, prompt: str, response: str) -> AssistantInteraction:
    """Create AI assistant interaction in database"""
    interaction = AssistantInteraction(
        user_id=user_id,
        prompt=prompt,
        response=response
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    
    # Update last interaction
    update_last_interaction(db, user_id)
    
    return interaction

def get_user_interactions(db: Session, user_id: int, limit: int = DefaultValues.INTERACTION_LIMIT) -> list[AssistantInteraction]:
    """Get recent user interactions with assistant"""
    return db.query(AssistantInteraction).filter(
        AssistantInteraction.user_id == user_id
    ).order_by(AssistantInteraction.interaction_timestamp.desc()).limit(limit).all()