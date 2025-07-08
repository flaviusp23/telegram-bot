"""Constants for the diabetes monitoring system database"""

# User Status Values
class UserStatusValues:
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

# Question Types
class QuestionTypes:
    DISTRESS_CHECK = "distress_check"
    SEVERITY_RATING = "severity_rating"

# Response Values
class ResponseValues:
    YES = "yes"
    NO = "no"
    # Severity ratings
    RATING_1 = "1"
    RATING_2 = "2"
    RATING_3 = "3"
    RATING_4 = "4"
    RATING_5 = "5"
    
    @classmethod
    def get_boolean_values(cls):
        return [cls.YES, cls.NO]
    
    @classmethod
    def get_rating_values(cls):
        return [cls.RATING_1, cls.RATING_2, cls.RATING_3, cls.RATING_4, cls.RATING_5]

# Database Settings
class DatabaseSettings:
    CHARSET = "utf8mb4"
    COLLATION = "utf8mb4_unicode_ci"

# Field Lengths
class FieldLengths:
    # User fields
    NAME_LENGTH = 100
    ENCRYPTED_FIELD_LENGTH = 500
    TELEGRAM_ID_LENGTH = 50
    
    # Response fields
    QUESTION_TYPE_LENGTH = 20
    RESPONSE_VALUE_LENGTH = 10

# Default Values
class DefaultValues:
    INTERACTION_LIMIT = 10

# Table Names
class TableNames:
    USERS = "users"
    RESPONSES = "responses"
    ASSISTANT_INTERACTIONS = "assistant_interactions"