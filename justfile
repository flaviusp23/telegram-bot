# Diabetes Monitoring System Commands
# https://github.com/casey/just

# Default command - show available commands
default:
    @just --list

# Setup virtual environment and install dependencies
setup:
    python3 -m venv venv
    source venv/bin/activate && pip install -r requirements.txt
    @echo "✅ Setup complete! Run 'just activate' to activate the virtual environment"

# Activate virtual environment (reminder command)
activate:
    @echo "Run: source venv/bin/activate"

# Run the bot with integrated scheduler (uses ENVIRONMENT from .env)
run:
    source venv/bin/activate && python run_bot.py

# Force development mode (overrides .env)
dev:
    source venv/bin/activate && ENVIRONMENT=DEV python run_bot.py

# Force production mode (overrides .env)
prod:
    source venv/bin/activate && ENVIRONMENT=PROD python run_bot.py

# Export data for a specific user
export user_id days="30":
    source venv/bin/activate && python run_export.py {{user_id}} --days {{days}}

# Run database migrations
migrate:
    source venv/bin/activate && alembic upgrade head

# Create a new database migration
make-migration message:
    source venv/bin/activate && alembic revision --autogenerate -m "{{message}}"

# Check bot health (requires bot to be running)
health:
    @echo "Send /health to your bot in Telegram to check status"

# View logs with tail
logs:
    tail -f *.log 2>/dev/null || echo "No log files found"

# Clean up cache files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    @echo "✅ Cleaned Python cache files"

# Stop all running bot processes
stop:
    pkill -f "python.*bot" || echo "No bot processes found"
    @echo "✅ Stopped all bot processes"

# Check if bot is running
status:
    @ps aux | grep -v grep | grep python | grep bot || echo "Bot is not running"

# Install dependencies
install:
    source venv/bin/activate && pip install -r requirements.txt

# Update requirements.txt with current packages
freeze:
    source venv/bin/activate && pip freeze > requirements.txt

# Run with environment variables from .env file
run-env:
    source venv/bin/activate && python run_bot.py

# Quick restart (stop and start)
restart: stop run

# Development restart (force dev mode)
restart-dev: stop dev

# Production restart (force prod mode)
restart-prod: stop prod

# Show environment variables
env:
    @echo "BOT_TOKEN: ${BOT_TOKEN:-(not set)}"
    @echo "ENVIRONMENT: ${ENVIRONMENT:-DEV}"
    @echo "DB_HOST: ${DB_HOST:-localhost}"
    @echo "DB_NAME: ${DB_NAME:-diabetes_monitoring}"

# Database console
db-console:
    mysql -h ${DB_HOST:-localhost} -u ${DB_USER:-root} -p ${DB_NAME:-diabetes_monitoring}

# Backup database
backup:
    mysqldump -h ${DB_HOST:-localhost} -u ${DB_USER:-root} -p ${DB_NAME:-diabetes_monitoring} > backup_$(date +%Y%m%d_%H%M%S).sql
    @echo "✅ Database backed up"

# Test bot commands (interactive)
test:
    @echo "Bot commands to test:"
    @echo "  /start - Start the bot"
    @echo "  /register - Register as new user"
    @echo "  /status - Check your status"
    @echo "  /questionnaire - Take questionnaire"
    @echo "  /pause - Pause alerts"
    @echo "  /resume - Resume alerts"
    @echo "  /export - Export your data"
    @echo "  /health - Check bot health"
    @echo "  /help - Show help"