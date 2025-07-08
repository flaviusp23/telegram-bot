# Diabetes Monitoring System

A Telegram bot system for monitoring diabetes-related distress through automatic questionnaires, built for the University of Málaga.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- MySQL 8.0+
- Telegram Bot Token (from @BotFather)
- Just command runner (`brew install just`)

### 1. Initial Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd diabetes-monitoring

# Setup environment and install dependencies
just setup

# Activate virtual environment
source venv/bin/activate
```

### 2. Configure Environment Variables
Create `.env` file:
```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=diabetes_monitoring

# Application Settings
ENVIRONMENT=DEV  # or PROD
ENCRYPTION_KEY=your_encryption_key_here
```

Generate encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Create Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "Diabetes Monitor")
4. Choose username ending in 'bot' (e.g., "diabetes_monitor_bot")
5. Copy token to `.env` file

### 4. Database Setup
```bash
# Run migrations
just migrate
```

### 5. Run the Application
```bash
# Run using ENVIRONMENT setting from .env file
just run

# Force development mode (questionnaires every 2 minutes)
just dev

# Force production mode (questionnaires at 9:00, 15:00, 21:00)
just prod
```

**Note**: The application will automatically validate your environment variables on startup. If any required variables are missing, you'll see a detailed error message explaining what needs to be configured.

## 📱 User Guide (Telegram)

### Getting Started
1. Find your bot on Telegram: @YourBotName
2. Start conversation: Send `/start`
3. Register: Send `/register`

### Available Commands
- `/start` - Welcome message and bot introduction
- `/register` - Register as a new user (required before using other features)
- `/status` - Check your registration status and alert settings
- `/questionnaire` - Take the distress questionnaire manually
- `/pause` - Stop receiving automatic questionnaires
- `/resume` - Resume receiving automatic questionnaires
- `/export` - Export your data as XML with graphs
- `/health` - Check if bot and scheduler are working
- `/help` - Show all available commands

### How Questionnaires Work
1. **Automatic Schedule**: 
   - DEV mode: Every 2 minutes (for testing)
   - PROD mode: 9:00 AM, 3:00 PM, 9:00 PM

2. **Question Flow**:
   - First: "Have you experienced diabetes-related distress today?" 
     - Click: **Yes** or **No**
   - If Yes: "On a scale of 1-5, how severe is your distress?"
     - Click: **1** (Very mild) to **5** (Very severe)

3. **Managing Alerts**:
   - Use `/pause` to stop automatic questionnaires
   - Use `/resume` to start them again
   - Use `/questionnaire` to take one manually anytime

### Data Export
Send `/export` to receive:
- Summary statistics
- XML file with all your responses
- Timeline graph showing distress over time
- Severity distribution pie chart
- Response rate graph
- Severity trend analysis

## 👨‍💻 Developer Guide

### Architecture Benefits

The recent refactoring brings several advantages:

1. **Modularity**: Each component has a single responsibility
2. **Maintainability**: Constants and configuration centralized
3. **Testability**: Smaller functions are easier to test
4. **Error Handling**: Consistent error handling patterns
5. **Type Safety**: Type hints throughout the codebase
6. **Code Reuse**: Decorators and utilities eliminate duplication

### Project Structure
```
diabetes-monitoring/
├── bot/
│   ├── __init__.py               # Bot module initialization
│   ├── main.py                   # Telegram bot with integrated APScheduler
│   ├── scheduler.py              # Scheduler configuration and jobs
│   ├── decorators.py             # Consolidated decorators for commands
│   ├── handlers/                 # Command handlers (modular structure)
│   │   ├── __init__.py
│   │   ├── auth.py              # Registration and authentication
│   │   ├── export.py            # Data export functionality
│   │   ├── questionnaire.py     # Questionnaire logic
│   │   └── user.py              # User-related commands
│   └── utils/                    # Bot utilities
│       ├── __init__.py
│       └── validators.py        # Input validation utilities
├── bot_config/                   # Bot configuration (renamed from config/)
│   ├── __init__.py
│   ├── bot_constants.py         # All bot constants and messages
│   └── validators.py            # Environment validation
├── database/
│   ├── __init__.py              # Database exports
│   ├── database.py              # Database connection
│   ├── models.py                # SQLAlchemy models
│   ├── encryption.py            # Field encryption with error handling
│   ├── helpers.py               # Database operations
│   ├── constants.py             # Database constants and enums
│   └── session_utils.py         # Session management utilities
├── scripts/
│   ├── __init__.py
│   ├── data_export.py           # Export functionality (modularized)
│   └── setup_database.py        # Database setup utilities
├── alembic/
│   └── versions/                # Database migrations
├── config.py                    # Main configuration file
├── run_bot.py                   # Main entry point with validation
├── run_export.py                # CLI export tool
├── requirements.txt             # Python dependencies
├── justfile                     # Command runner
├── .env                         # Environment variables (don't commit!)
└── README.md                    # This file
```

### Common Commands (Using Just)

#### Running the Bot
```bash
# Show all available commands
just

# Run the bot (uses ENVIRONMENT from .env)
just run

# Force development mode (alerts every 2 minutes, overrides .env)
just dev

# Force production mode (alerts at 9:00, 15:00, 21:00, overrides .env)
just prod

# Check if bot is running
just status

# Stop the bot
just stop

# Restart the bot
just restart          # Uses .env setting
just restart-dev      # Forces dev mode
just restart-prod     # Forces prod mode
```

#### Database Operations
```bash
# Run migrations
just migrate

# Create new migration
just make-migration "add new feature"

# Access MySQL console
just db-console

# Backup database
just backup
```

#### Data Export (CLI)
```bash
# Export last 30 days for user ID 1
just export 1

# Export last 60 days for user ID 1
just export 1 60

# Or directly:
python run_export.py <user_id> --days 30
```

#### Maintenance
```bash
# Clean Python cache files
just clean

# Install/update dependencies
just install

# Update requirements.txt
just freeze

# View current environment variables
just env
```

### How It Works

1. **Single Process Architecture**: 
   - Bot and scheduler run in one process using APScheduler
   - No more event loop issues!

2. **Scheduler**: 
   - APScheduler (AsyncIOScheduler) for reliable async scheduling
   - Handles timezone properly
   - Coalesces missed jobs

3. **Database**: 
   - MySQL with SQLAlchemy ORM
   - Alembic for migrations
   - Automatic encryption for sensitive fields
   - Session management utilities for cleaner code

4. **User States**: 
   - `active`: Receives automatic questionnaires
   - `inactive`: Paused (manual questionnaires only)
   - `blocked`: User blocked the bot

### Recent Improvements

#### Code Organization
- **Modular structure**: Bot code split into `handlers/`, `utils/`, and other logical modules
- **Renamed config directory**: Changed to `bot_config/` to avoid Python naming conflicts
- **Consolidated decorators**: All decorators now in single `bot/decorators.py` file
- **Professional naming conventions**: Snake_case for variables, descriptive function names

#### New Features
- **Environment validation**: Automatic validation on startup ensures all required variables are set
- **Enhanced error handling**: Better encryption error handling with user-friendly messages
- **Constants system**: Centralized constants in `bot_config/bot_constants.py` for easy maintenance
- **Database utilities**: New `session_utils.py` with context managers and decorators

#### Code Quality
- **Split complex functions**: Large functions like `export_data` broken into smaller, focused functions
- **Type hints**: Added throughout for better IDE support
- **Comprehensive logging**: Structured logging with appropriate levels
- **Error recovery**: Graceful handling of database and Telegram API errors

### Environment Modes

#### Development Mode (`ENVIRONMENT=DEV`)
- Questionnaires every 2 minutes
- Perfect for testing
- Faster feedback loop

#### Production Mode (`ENVIRONMENT=PROD`)
- Questionnaires at 9:00, 15:00, 21:00
- Real schedule for actual patients
- Timezone aware

### Troubleshooting

#### Bot won't start
```bash
# Check environment variables
just env

# Verify MySQL is running
mysql -u root -p -e "SELECT 1"

# Check bot token (should show bot info)
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Look for errors
just run
```

#### Database connection errors
```bash
# Test connection
mysql -h localhost -u root -p diabetes_monitoring

# Run migrations
just migrate

# Check database exists
mysql -u root -p -e "SHOW DATABASES LIKE 'diabetes_monitoring'"
```

#### Bot not sending alerts
1. Check user status with `/status` - must show "Active"
2. Verify environment mode in logs
3. Use `/health` command to check scheduler
4. Check logs for errors

#### Multiple bot instances error
```bash
# Kill all bot processes
just stop

# Wait a few seconds, then start again
just run
```

### Testing the System

1. **Quick Test (Development)**:
   ```bash
   # Force dev mode for 2-minute alerts
   just dev
   # OR set in .env and run normally
   just run
   ```

2. **Test Commands in Telegram**:
   - `/start` - Should show welcome
   - `/register` - Should register you
   - `/status` - Should show your status
   - `/questionnaire` - Should start questionnaire
   - `/health` - Should show bot health

3. **Test Scheduler**:
   - In DEV mode, wait 2 minutes for automatic alert
   - Check logs for "Alert job completed"

## 🔒 Security

- **Encryption**: Sensitive data (passport, phone, email) encrypted with Fernet
- **Encryption Key Validation**: Automatic validation ensures encryption key is properly set
- **Error Handling**: Graceful handling of encryption/decryption errors
- **Environment Variables**: All secrets in `.env` (never commit!)
- **User Identification**: Uses Telegram IDs
- **Database Security**: Prepared statements, parameterized queries
- **Session Management**: Automatic cleanup and proper transaction handling

## 📊 Features

### Implemented ✅
- Telegram bot with full command set
- Automatic questionnaires with APScheduler
- Manual questionnaire option
- Pause/resume functionality
- Data export (XML + graphs)
- Encrypted sensitive data
- Production-ready scheduler (no event loop issues!)
- User status management (active/inactive/blocked)
- Health monitoring

### Coming Soon 🔄
- LLM Integration for emotional support
- Advanced analytics
- Multi-language support

## 📈 Data Export

### For Users (Telegram)
Send `/export` to get your data instantly!

### For Developers (CLI)
```bash
# Export by user ID
just export 1

# Export with custom days
just export 1 60

# Direct command with more options
python run_export.py 1 --days 30 --output-dir custom_exports/
```

### Export Contents
- **Statistics**: Response rate, distress frequency, severity averages
- **XML File**: Complete structured data with proper formatting
- **Graphs** (generated using modular functions): 
  - Distress timeline
  - Severity distribution
  - Response rate
  - Severity trend
- **Error handling**: Graceful fallback if graph generation fails

## 🚨 Important Notes

1. **Never commit `.env` file** - Contains secrets!
2. **Python 3.13 Compatibility** - JobQueue disabled due to weak reference issue
3. **Single Process** - Don't run multiple instances
4. **Timezone** - Scheduler uses system timezone

## 📝 License

This project was developed for educational purposes at the University of Málaga.

---

**Developed by**: Flavius Paltin  
**Supervisor**: Miguel  
**Institution**: University of Málaga  
**Framework**: Telegram Bot with APScheduler Integration