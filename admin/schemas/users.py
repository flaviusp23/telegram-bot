"""
Pydantic schemas for patient-related endpoints.
"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field, EmailStr, validator

class UserBase(BaseModel):
    """Base patient schema."""
    first_name: str
    family_name: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class UserResponse(UserBase):
    """Patient response schema for list views."""
    id: int
    telegram_id: str
    status: str
    registration_date: datetime
    last_interaction: Optional[datetime] = None
    response_count: int = 0
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed patient response with additional fields."""
    interaction_count: int = 0
    recent_responses: List[dict] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Patient update request schema."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    family_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, pattern="^(active|inactive|blocked)$")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, +, - and spaces')
        return v


class ResponseModel(BaseModel):
    """Response model for patient questionnaire responses."""
    id: int
    question_type: str
    response_value: Any
    response_timestamp: datetime
    
    class Config:
        from_attributes = True


class InteractionModel(BaseModel):
    """Model for patient-AI chat interactions."""
    id: int
    prompt: str
    response: str
    interaction_timestamp: datetime
    
    class Config:
        from_attributes = True


class PaginatedUsers(BaseModel):
    """Paginated patient list response."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int