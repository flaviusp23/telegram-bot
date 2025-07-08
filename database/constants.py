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
    DISTRESS_CHECK = "distress_check"
    SEVERITY_RATING = "severity_rating"
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all question types"""
        return [cls.DISTRESS_CHECK, cls.SEVERITY_RATING]

# Response Values
class ResponseValues:
    """Possible response values for questions"""
    # Boolean responses
    YES = "yes"
    NO = "no"
    
    # Severity ratings
    RATING_1 = "1"
    RATING_2 = "2"
    RATING_3 = "3"
    RATING_4 = "4"
    RATING_5 = "5"
    
    # Severity levels (for easier categorization)
    SEVERITY_VERY_MILD = 1
    SEVERITY_MILD = 2
    SEVERITY_MODERATE = 3
    SEVERITY_SEVERE = 4
    SEVERITY_VERY_SEVERE = 5
    
    # Severity ranges
    MILD_SEVERITY_RANGE = [1, 2]
    MODERATE_SEVERITY_RANGE = [3]
    HIGH_SEVERITY_RANGE = [4, 5]
    
    @classmethod
    def get_boolean_values(cls) -> List[str]:
        """Get boolean response values"""
        return [cls.YES, cls.NO]
    
    @classmethod
    def get_rating_values(cls) -> List[str]:
        """Get severity rating values"""
        return [cls.RATING_1, cls.RATING_2, cls.RATING_3, cls.RATING_4, cls.RATING_5]
    
    @classmethod
    def get_numeric_ratings(cls) -> List[int]:
        """Get numeric severity ratings"""
        return [cls.SEVERITY_VERY_MILD, cls.SEVERITY_MILD, cls.SEVERITY_MODERATE, 
                cls.SEVERITY_SEVERE, cls.SEVERITY_VERY_SEVERE]

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

