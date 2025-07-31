"""Bot-specific constants for the diabetes monitoring system"""

# Alert Settings
class AlertSettings:
    """Constants for alert scheduling"""
    # Development mode alert interval (minutes)
    DEV_ALERT_INTERVAL_MINUTES = 2
    
    # Production alert times (24-hour format)
    PROD_ALERT_TIMES = [
        {'hour': 9, 'minute': 0},   # 9:00 AM
        {'hour': 15, 'minute': 0},  # 3:00 PM
        {'hour': 21, 'minute': 0}   # 9:00 PM
    ]
    
    # Expected responses per day for response rate calculation
    EXPECTED_RESPONSES_PER_DAY = 3
    
    # Message delay between bulk sends (seconds)
    MESSAGE_DELAY_SECONDS = 0.5


# Bot Messages
class BotMessages:
    """All bot message templates"""
    
    # Start command messages
    WELCOME_BACK = (
        "Welcome back, {first_name}! 👋\n\n"
        "I'm here to help you manage diabetes-related distress.\n"
        "Use /help to see available commands."
    )
    
    WELCOME_NEW = (
        "Hello {first_name}! 👋\n\n"
        "I'm a diabetes monitoring assistant designed to help track and manage "
        "diabetes-related distress.\n\n"
        "To get started, please register using /register"
    )
    
    # Registration messages
    ALREADY_REGISTERED = "You're already registered, {first_name}! ✅"
    
    REGISTRATION_SUCCESS = (
        "Registration successful! 🎉\n\n"
        "Welcome {first_name}!\n\n"
        "You'll receive questionnaires at scheduled times to help monitor "
        "your diabetes-related distress.\n\n"
        "Use /help to see available commands."
    )
    
    REGISTRATION_ERROR = "Sorry, there was an error during registration. Please try again later."
    
    # Help command
    HELP_TEXT = """Available commands:

/start - Start the bot
/register - Register as a new user
/status - Check your registration status
/pause - Pause automatic questionnaires
/resume - Resume automatic questionnaires
/questionnaire - Complete the DDS-2 questionnaire
/support - Chat with AI emotional support assistant
/export - Export your data (XML + graphs)
/health - Check bot health status
/help - Show this help message

🤖 AI Support: After completing each questionnaire, you'll be offered a chance to chat with our AI assistant powered by LLaMA 3.2 for emotional support.

The questionnaire uses the validated DDS-2 scale:
• 2 questions about diabetes distress
• Scale from 1 (not a problem) to 6 (serious problem)
• Available in English and Spanish"""
    
    # Health check messages
    HEALTH_STATUS_TEMPLATE = """🏥 Bot Health Status

✅ Bot: Online
✅ Scheduler: {scheduler_status}
📅 Environment: {environment}
⏰ Scheduled Jobs: {job_count}"""
    
    HEALTH_DEV_MODE = "\n🔧 DEV Mode: Alerts every {minutes} minutes"
    HEALTH_PROD_MODE = "\n🏭 PROD Mode: Alerts at 9:00, 15:00, 21:00"
    
    # Status command messages
    NOT_REGISTERED = "You're not registered yet. Use /register to get started!"
    
    STATUS_TEMPLATE = """📊 Your Status:

Name: {first_name} {family_name}
Alert Status: {alert_status}
Registered: {registration_date}
Last interaction: {last_interaction}

Commands:
• Use /pause to stop automatic questionnaires
• Use /resume to start receiving them again
• Use /questionnaire to complete one manually"""
    
    # Alert status messages
    ALERT_STATUS_ACTIVE = "✅ Active - Receiving automatic questionnaires"
    ALERT_STATUS_INACTIVE = "⏸️ Paused - Not receiving automatic questionnaires"
    ALERT_STATUS_BLOCKED = "🚫 Blocked - Cannot receive messages"
    
    # Pause/Resume messages
    PAUSE_ALREADY_PAUSED = "⏸️ Your automatic questionnaires are already paused."
    
    PAUSE_SUCCESS = (
        "⏸️ Automatic questionnaires have been paused.\n\n"
        "You will no longer receive scheduled questionnaires.\n"
        "You can still complete questionnaires manually with /questionnaire\n"
        "Use /resume to start receiving automatic questionnaires again."
    )
    
    RESUME_ALREADY_ACTIVE = "✅ Your automatic questionnaires are already active."
    
    RESUME_BLOCKED = (
        "❌ Cannot resume - you have blocked the bot.\n"
        "Please unblock the bot in Telegram settings first."
    )
    
    RESUME_SUCCESS = (
        "✅ Automatic questionnaires have been resumed!\n\n"
        "You will now receive questionnaires at scheduled times.\n"
        "Use /pause if you need to stop them again."
    )
    
    # Questionnaire messages
    PLEASE_REGISTER_FIRST = "Please register first using /register"
    
    # DDS-2 Questionnaire messages
    DDS2_INTRO = (
        "Hello {user_name}! 👋\n\n"
        "Time for your diabetes distress check.\n\n"
        "I'll ask you 2 quick questions about how diabetes has been affecting you.\n"
        "Please rate each on a scale from 1 to 6:\n"
        "• 1 = Not a problem\n"
        "• 6 = Very serious problem"
    )
    
    DDS2_Q1_OVERWHELMED = (
        "Question 1 of 2:\n\n"
        "Feeling overwhelmed by the demands of living with diabetes\n"
        "(Me siento agobiado por las exigencias de vivir con diabetes)\n\n"
        "How much of a problem is this for you?"
    )
    
    DDS2_Q2_FAILING = (
        "Question 2 of 2:\n\n"
        "Feeling that I am often failing with my diabetes regimen\n"
        "(Siento que a menudo estoy fallando con mi rutina de diabetes)\n\n"
        "How much of a problem is this for you?"
    )
    
    # DDS-2 Response messages based on total score
    DDS2_LOW_DISTRESS_RESPONSE = (
        "Thank you for completing the questionnaire! 😊\n\n"
        "Your responses indicate low diabetes distress. That's great!\n"
        "Keep up the good work with your diabetes management.\n\n"
        "I'll check in with you again at the next scheduled time."
    )
    
    DDS2_MODERATE_DISTRESS_RESPONSE = (
        "Thank you for completing the questionnaire. 💙\n\n"
        "Your responses indicate moderate diabetes distress.\n"
        "It's normal to feel challenged by diabetes management sometimes.\n\n"
        "Consider taking some time for self-care today."
    )
    
    DDS2_HIGH_DISTRESS_RESPONSE = (
        "Thank you for sharing your feelings. 🫂\n\n"
        "Your responses indicate high diabetes distress.\n"
        "Please consider reaching out to your healthcare team for support.\n\n"
        "Remember, you don't have to manage this alone."
    )
    
    # Legacy questionnaire messages (kept for backwards compatibility)
    QUESTIONNAIRE_START = (
        "Hello {user_name}! 👋\n\n"
        "Time for your diabetes distress check.\n\n"
        "Have you experienced diabetes-related distress today?"
    )
    
    SCHEDULED_QUESTIONNAIRE_START = (
        "Hello {first_name}! 👋\n\n"
        "Time for your scheduled diabetes distress check.\n\n"
        "Have you experienced diabetes-related distress today?"
    )
    
    # Legacy distress response messages
    NO_DISTRESS_RESPONSE = (
        "Great to hear you're doing well! 😊\n\n"
        "Keep up the good work with your diabetes management.\n"
        "I'll check in with you again later."
    )
    
    DISTRESS_SEVERITY_QUESTION = (
        "I'm sorry to hear you're experiencing distress. 💙\n\n"
        "On a scale of 1-5, how severe is your distress?\n\n"
        "1 = Very mild\n"
        "5 = Very severe"
    )
    
    # Legacy severity response messages
    SEVERITY_MILD_RESPONSE = (
        "Thank you for sharing. It's good that your distress is relatively mild. 🌟\n\n"
        "Remember, it's normal to experience some distress with diabetes management.\n"
        "Keep using your coping strategies!"
    )
    
    SEVERITY_MODERATE_RESPONSE = (
        "Thank you for sharing. Moderate distress can be challenging. 💪\n\n"
        "Consider taking a few minutes for self-care today."
    )
    
    SEVERITY_HIGH_RESPONSE = (
        "I'm concerned about your high distress level. 🫂\n\n"
        "Please consider reaching out to your healthcare team or a mental health professional.\n"
        "Remember, you don't have to manage this alone."
    )
    
    # Export messages
    EXPORT_GENERATING = (
        "📊 Generating your data export...\n"
        "This may take a moment. I'll send you the files when ready."
    )
    
    EXPORT_SUMMARY_TEMPLATE = """📊 **Your Data Export Summary**
Period: {start_date} to {end_date}

**Statistics:**
• Total responses: {total_responses}
• Distress occurrences: {distress_count} ({distress_percentage:.1f}%)
• Average severity: {average_severity}
• Response rate: {response_rate:.1f}%

**Severity Distribution:**
"""
    
    EXPORT_XML_CAPTION = "📄 Your complete data in XML format"
    
    EXPORT_COMPLETE = (
        "✅ Export complete! All your data has been sent above.\n\n"
        "💡 Tip: You can save these files for your records or share them with your healthcare provider."
    )
    
    # Error messages
    ERROR_GENERIC = "Sorry, there was an error. Please try again later."
    ERROR_RECORDING_RESPONSE = "Sorry, there was an error recording your response. Please try again later."
    ERROR_EXPORT = "Sorry, there was an error generating your export. Please try again later."
    ERROR_USER_NOT_FOUND = "User not found. Please register with /register"
    
    # Admin messages
    SEND_ALERTS_START = "🔔 Sending alerts to all active users..."
    SEND_ALERTS_COMPLETE = "✅ Alert job completed"
    ADMIN_ONLY_ACCESS = "❌ You don't have permission to use this command."
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "⏱️ Rate limit exceeded. Please wait a moment before trying again."


# Button Labels
class ButtonLabels:
    """Labels for inline keyboard buttons"""
    # Legacy labels
    YES = "Yes"
    NO = "No"
    
    # Legacy severity labels (1-5 scale)
    SEVERITY_1 = "1 - Very mild"
    SEVERITY_2 = "2 - Mild"
    SEVERITY_3 = "3 - Moderate"
    SEVERITY_4 = "4 - Severe"
    SEVERITY_5 = "5 - Very severe"
    
    # DDS-2 scale labels (1-6)
    DDS2_1 = "1"
    DDS2_2 = "2"
    DDS2_3 = "3"
    DDS2_4 = "4"
    DDS2_5 = "5"
    DDS2_6 = "6"


# Callback Data
class CallbackData:
    """Callback data values for inline keyboards"""
    # Legacy callback data
    DISTRESS_YES = "distress_yes"
    DISTRESS_NO = "distress_no"
    SEVERITY_PREFIX = "severity_"
    
    # DDS-2 callback data
    DDS2_PREFIX = "dds2_"
    DDS2_Q1_PREFIX = "dds2_q1_"
    DDS2_Q2_PREFIX = "dds2_q2_"
    
    @classmethod
    def severity(cls, level: int) -> str:
        """Generate legacy severity callback data"""
        return f"{cls.SEVERITY_PREFIX}{level}"
    
    @classmethod
    def dds2_q1(cls, level: int) -> str:
        """Generate DDS-2 question 1 callback data"""
        return f"{cls.DDS2_Q1_PREFIX}{level}"
    
    @classmethod
    def dds2_q2(cls, level: int) -> str:
        """Generate DDS-2 question 2 callback data"""
        return f"{cls.DDS2_Q2_PREFIX}{level}"


# Export Settings
class ExportSettings:
    """Constants for data export functionality"""
    DEFAULT_EXPORT_DAYS = 30
    MAX_EXPORT_DAYS = 365  # Maximum days for export
    MIN_EXPORT_DAYS = 1    # Minimum days for export
    EXPORT_DIR_PREFIX = "temp_exports"
    XML_FILENAME = "data_export.xml"
    
    # Export cleanup
    EXPORT_CLEANUP_HOURS = 24  # Delete exports after 24 hours
    
    # Graph filenames and captions
    GRAPHS = [
        ('distress_timeline.png', '📈 Distress Timeline'),
        ('severity_distribution.png', '🥧 Severity Distribution'),
        ('response_rate.png', '📊 Daily Response Rate'),
        ('severity_trend.png', '📉 Severity Trend')
    ]
    
    # Graph settings
    SEVERITY_TREND_WINDOW = 7  # Moving average window
    
    # Graph colors
    SEVERITY_COLORS = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#c0392b']
    RESPONSE_RATE_COLOR = '#3498db'
    
    # Graph quality settings
    GRAPH_DPI = 100
    GRAPH_QUALITY = 95  # JPEG quality percentage


# Bot Settings
class BotSettings:
    """General bot configuration constants"""
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Job IDs for scheduler
    DEV_ALERT_JOB_ID = 'dev_alerts'
    PROD_ALERT_JOB_PREFIX = 'prod_alert_'
    
    # Date/Time formats
    DATETIME_FORMAT = '%Y-%m-%d %H:%M'
    DATE_FORMAT = '%Y-%m-%d'
    TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
    
    # Response rate calculation
    MAX_RESPONSE_RATE_PERCENT = 100.0
    
    # Scheduler settings
    SCHEDULER_COALESCE = True
    SCHEDULER_MAX_INSTANCES = 1
    
    # Bot timeouts
    CONVERSATION_TIMEOUT = 300  # 5 minutes for conversation handlers
    REQUEST_TIMEOUT = 30  # 30 seconds for API requests
    
    # Rate limiting
    MAX_COMMANDS_PER_MINUTE = 10
    MAX_EXPORTS_PER_DAY = 5
    
    # File size limits
    MAX_EXPORT_FILE_SIZE_MB = 10
    MAX_IMAGE_SIZE_MB = 5


# Logging Messages
class LogMessages:
    """Log message templates"""
    BOT_STARTING = "🚀 Starting Diabetes Monitoring Bot with integrated scheduler..."
    BOT_ENVIRONMENT = "📅 Environment: {environment}"
    BOT_INITIALIZING = "Initializing bot with scheduler - Environment: {environment}"
    
    SCHEDULER_DEV_MODE = "🔧 DEV MODE: Scheduled alerts every {minutes} minutes"
    SCHEDULER_PROD_MODE = "🏭 PROD MODE: Scheduled alerts at 9:00, 15:00, 21:00"
    SCHEDULER_STARTED = "✅ Scheduler started successfully"
    SCHEDULER_STOPPING = "Shutting down scheduler..."
    SCHEDULER_STOPPED = "✅ Scheduler stopped"
    
    ALERT_JOB_START = "🔔 Starting scheduled alert job..."
    ALERT_JOB_NO_USERS = "No active users to send alerts to"
    ALERT_JOB_FOUND_USERS = "Found {count} active users"
    ALERT_JOB_COMPLETE = "📊 Alert job completed: Sent: {sent}, Failed: {failed}"
    
    QUESTIONNAIRE_SENT = "✅ Sent questionnaire to {first_name} (ID: {telegram_id})"
    USER_BLOCKED_BOT = "⚠️ User {first_name} (ID: {telegram_id}) has blocked the bot"
    USER_STATUS_UPDATED = "Updated user {telegram_id} status to blocked"
    
    ERROR_REGISTRATION = "Registration error: {error}"
    ERROR_PAUSING_ALERTS = "Error pausing alerts: {error}"
    ERROR_RESUMING_ALERTS = "Error resuming alerts: {error}"
    ERROR_RECORDING_RESPONSE = "Error recording response: {error}"
    ERROR_RECORDING_SEVERITY = "Error recording severity: {error}"
    ERROR_EXPORT = "Export error: {error}"
    ERROR_SCHEDULED_ALERT = "❌ Error in scheduled alert job: {error}"
    ERROR_SEND_USER = "❌ Error sending to {telegram_id}: {error}"
    ERROR_BAD_REQUEST = "❌ Bad request for user {telegram_id}: {error}"
    ERROR_UPDATE = "Update {update} caused error {error}"
    
    WARNING_GRAPHS_NOT_GENERATED = "Could not generate graphs: {error}"


# XML Export Constants
class XMLConstants:
    """Constants for XML export"""
    ROOT_ELEMENT = "diabetes_monitoring_export"
    VERSION = "1.0"
    
    # Element names
    USER_ELEMENT = "user"
    EXPORT_PERIOD_ELEMENT = "export_period"
    STATISTICS_ELEMENT = "statistics"
    SEVERITY_DISTRIBUTION_ELEMENT = "severity_distribution"
    RESPONSES_ELEMENT = "responses"
    RESPONSE_ELEMENT = "response"
    LEVEL_ELEMENT = "level"
    
    # Field names
    ID_FIELD = "ID"
    FIRST_NAME_FIELD = "first_name"
    FAMILY_NAME_FIELD = "family_name"
    TELEGRAM_ID_FIELD = "telegram_id"
    STATUS_FIELD = "Status"
    REGISTRATION_DATE_FIELD = "registration_date"
    START_DATE_FIELD = "start_date"
    END_DATE_FIELD = "end_date"
    TIMESTAMP_FIELD = "Timestamp"
    QUESTION_TYPE_FIELD = "question_type"
    RESPONSE_VALUE_FIELD = "response_value"
    
    # Statistics fields
    TOTAL_RESPONSES_FIELD = "total_responses"
    DISTRESS_COUNT_FIELD = "distress_count"
    NO_DISTRESS_COUNT_FIELD = "no_distress_count"
    DISTRESS_PERCENTAGE_FIELD = "distress_percentage"
    AVERAGE_SEVERITY_FIELD = "average_severity"
    MAX_SEVERITY_FIELD = "max_severity"
    MIN_SEVERITY_FIELD = "min_severity"
    RESPONSE_RATE_FIELD = "response_rate"
    
    # Attributes
    GENERATED_ATTR = "generated"
    VERSION_ATTR = "version"
    VALUE_ATTR = "value"
    
    # Formatting
    PERCENTAGE_FORMAT = "{:.2f}"
    INDENT_SPACES = "  "


# Graph Settings
class GraphSettings:
    """Settings for graph generation"""
    # Figure sizes
    TIMELINE_FIGURE_SIZE = (12, 6)
    PIE_FIGURE_SIZE = (8, 8)
    BAR_FIGURE_SIZE = (12, 6)
    TREND_FIGURE_SIZE = (12, 6)
    
    # Labels and titles
    DISTRESS_TIMELINE_TITLE = 'Distress Check Timeline - {first_name} {family_name}'
    SEVERITY_DISTRIBUTION_TITLE = 'Severity Distribution - {first_name} {family_name}'
    RESPONSE_RATE_TITLE = 'Daily Response Rate - {first_name} {family_name}'
    SEVERITY_TREND_TITLE = 'Severity Trend - {first_name} {family_name}'
    
    # Axis labels
    DATE_LABEL = 'Date'
    DISTRESS_LABEL = 'Distress (0=No, 1=Yes)'
    RESPONSE_RATE_LABEL = 'Response Rate (%)'
    SEVERITY_LEVEL_LABEL = 'Severity Level'
    
    # Legend labels
    EXPECTED_RATE_LABEL = 'Expected (100%)'
    INDIVIDUAL_RATINGS_LABEL = 'Individual Ratings'
    MOVING_AVERAGE_LABEL = '7-Point Moving Average'
    
    # Y-axis ticks
    DISTRESS_Y_TICKS = ([0, 1], ['No', 'Yes'])
    SEVERITY_Y_TICKS = range(1, 6)
    
    # Other settings
    SCATTER_ALPHA = 0.6
    SCATTER_SIZE = 100
    LINE_ALPHA = 0.3
    BAR_ALPHA = 0.7
    GRID_ALPHA = 0.3
    EXPECTED_LINE_ALPHA = 0.5
    
    RESPONSE_RATE_Y_MAX = 120
    DISTRESS_Y_MIN = -0.1
    DISTRESS_Y_MAX = 1.1
    SEVERITY_Y_MIN = 0.5
    SEVERITY_Y_MAX = 5.5
    
    DATE_ROTATION = 45
    DATE_INTERVAL_DAYS = 7
    PIE_START_ANGLE = 90
    AUTOPCT_FORMAT = '%1.1f%%'