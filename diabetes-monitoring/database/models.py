from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
from database.encryption import EncryptedType
from database.constants import UserStatusValues, FieldLengths, TableNames
import enum

class UserStatus(enum.Enum):
    active = UserStatusValues.ACTIVE
    inactive = UserStatusValues.INACTIVE
    blocked = UserStatusValues.BLOCKED

class User(Base):
    __tablename__ = TableNames.USERS
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(FieldLengths.NAME_LENGTH), nullable=False)
    family_name = Column(String(FieldLengths.NAME_LENGTH), nullable=False)
    passport_id = Column(EncryptedType(FieldLengths.ENCRYPTED_FIELD_LENGTH), unique=True)
    phone_number = Column(EncryptedType(FieldLengths.ENCRYPTED_FIELD_LENGTH))
    telegram_id = Column(String(FieldLengths.TELEGRAM_ID_LENGTH), unique=True, nullable=False)
    email = Column(EncryptedType(FieldLengths.ENCRYPTED_FIELD_LENGTH))
    status = Column(Enum(UserStatus), default=UserStatus.active)
    registration_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_interaction = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    responses = relationship("Response", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("AssistantInteraction", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.first_name} {self.family_name}, telegram_id={self.telegram_id})>"

class Response(Base):
    __tablename__ = TableNames.RESPONSES
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(f"{TableNames.USERS}.id"), nullable=False)
    question_type = Column(String(FieldLengths.QUESTION_TYPE_LENGTH), nullable=False)  # 'distress_check' or 'severity_rating'
    response_value = Column(String(FieldLengths.RESPONSE_VALUE_LENGTH), nullable=False)  # 'yes'/'no' or '1'-'5'
    response_timestamp = Column(TIMESTAMP, server_default=func.current_timestamp())
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="responses")
    
    def __repr__(self):
        return f"<Response(id={self.id}, user_id={self.user_id}, type={self.question_type}, value={self.response_value})>"

class AssistantInteraction(Base):
    __tablename__ = TableNames.ASSISTANT_INTERACTIONS
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(f"{TableNames.USERS}.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    interaction_timestamp = Column(TIMESTAMP, server_default=func.current_timestamp())
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    
    def __repr__(self):
        return f"<AssistantInteraction(id={self.id}, user_id={self.user_id})>"