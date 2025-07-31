"""Constants for the diabetes monitoring system database"""
from typing import List

# User Status Values
class UserStatusValues:
    """Possible status values for users"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all possible status values"""
        return [cls.ACTIVE, cls.INACTIVE, cls.BLOCKED]

# Question Types
class QuestionTypes:
    """Types of questions in the monitoring system"""
    # DDS-2 question types
    DDS2_Q1_OVERWHELMED = "dds2_q1_overwhelmed"
    DDS2_Q2_FAILING = "dds2_q2_failing"
    
    # Legacy question types (kept for backwards compatibility)
    DISTRESS_CHECK = "distress_check"
    SEVERITY_RATING = "severity_rating"
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all question types"""
        return [cls.DDS2_Q1_OVERWHELMED, cls.DDS2_Q2_FAILING,
                cls.DISTRESS_CHECK, cls.SEVERITY_RATING]
    
    @classmethod
    def get_dds2_types(cls) -> List[str]:
        """Get DDS-2 question types"""
        return [cls.DDS2_Q1_OVERWHELMED, cls.DDS2_Q2_FAILING]

# Response Values
class ResponseValues:
    """Possible response values for questions"""
    # Boolean responses (legacy)
    YES = "yes"
    NO = "no"
    
    # DDS-2 ratings (1-6 scale)
    DDS2_1 = "1"  # Not a problem
    DDS2_2 = "2"  # A slight problem
    DDS2_3 = "3"  # A moderate problem
    DDS2_4 = "4"  # Somewhat serious problem
    DDS2_5 = "5"  # A serious problem
    DDS2_6 = "6"  # A very serious problem
    
    # Legacy severity ratings (1-5)
    RATING_1 = "1"
    RATING_2 = "2"
    RATING_3 = "3"
    RATING_4 = "4"
    RATING_5 = "5"
    
    # DDS-2 score thresholds
    DDS2_LOW_DISTRESS_THRESHOLD = 4   # Score 2-4: Low distress
    DDS2_MODERATE_DISTRESS_THRESHOLD = 8  # Score 5-8: Moderate distress
    # Score 9-12: High distress
    
    # Legacy severity levels (for backwards compatibility)
    SEVERITY_VERY_MILD = 1
    SEVERITY_MILD = 2
    SEVERITY_MODERATE = 3
    SEVERITY_SEVERE = 4
    SEVERITY_VERY_SEVERE = 5
    
    # Legacy severity ranges
    MILD_SEVERITY_RANGE = [1, 2]
    MODERATE_SEVERITY_RANGE = [3]
    HIGH_SEVERITY_RANGE = [4, 5]
    
    @classmethod
    def get_boolean_values(cls) -> List[str]:
        """Get boolean response values"""
        return [cls.YES, cls.NO]
    
    @classmethod
    def get_dds2_values(cls) -> List[str]:
        """Get DDS-2 rating values (1-6)"""
        return [cls.DDS2_1, cls.DDS2_2, cls.DDS2_3, cls.DDS2_4, cls.DDS2_5, cls.DDS2_6]
    
    @classmethod
    def get_rating_values(cls) -> List[str]:
        """Get legacy severity rating values (1-5)"""
        return [cls.RATING_1, cls.RATING_2, cls.RATING_3, cls.RATING_4, cls.RATING_5]
    
    @classmethod
    def get_numeric_ratings(cls) -> List[int]:
        """Get numeric severity ratings"""
        return [cls.SEVERITY_VERY_MILD, cls.SEVERITY_MILD, cls.SEVERITY_MODERATE, 
                cls.SEVERITY_SEVERE, cls.SEVERITY_VERY_SEVERE]
    
    @classmethod
    def calculate_dds2_distress_level(cls, total_score: int) -> str:
        """Calculate distress level from DDS-2 total score (2-12)"""
        if total_score <= cls.DDS2_LOW_DISTRESS_THRESHOLD:
            return "low"
        elif total_score <= cls.DDS2_MODERATE_DISTRESS_THRESHOLD:
            return "moderate"
        else:
            return "high"

# Database Settings
class DatabaseSettings:
    """Database configuration constants"""
    CHARSET = "utf8mb4"
    COLLATION = "utf8mb4_unicode_ci"
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600

# Field Lengths
class FieldLengths:
    """Maximum field lengths for database columns"""
    # User fields
    NAME_LENGTH = 100
    ENCRYPTED_FIELD_LENGTH = 500
    TELEGRAM_ID_LENGTH = 50
    EMAIL_LENGTH = 255
    PHONE_LENGTH = 20
    PASSPORT_LENGTH = 50
    STATUS_LENGTH = 20
    
    # Response fields
    QUESTION_TYPE_LENGTH = 20
    RESPONSE_VALUE_LENGTH = 10
    
    # Assistant interaction fields
    INTERACTION_TYPE_LENGTH = 20
    MESSAGE_LENGTH = 5000  # For longer AI conversations

# Default Values
class DefaultValues:
    """Default values for database fields"""
    INTERACTION_LIMIT = 10
    USER_STATUS = UserStatusValues.ACTIVE
    DEFAULT_NAME = "User"
    DEFAULT_FAMILY_NAME = "Unknown"

# Table Names
class TableNames:
    """Database table names"""
    USERS = "users"
    RESPONSES = "responses"
    ASSISTANT_INTERACTIONS = "assistant_interactions"

