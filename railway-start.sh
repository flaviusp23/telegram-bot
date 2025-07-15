#!/bin/bash

# Railway startup script for the diabetes monitoring system
# Runs database migrations and starts both bot and admin services

set -e

echo "🚀 Starting Diabetes Monitoring System on Railway..."

# Run database migrations
echo "📊 Running database migrations..."
alembic upgrade head

# Create admin user
echo "👤 Creating admin user..."
python scripts/create_admin_simple.py

# In Railway, we only expose the admin interface on the main PORT
# The bot runs in the background
echo "🤖 Starting Telegram bot in background..."
python run_bot.py &

echo "🔧 Starting admin interface on port ${PORT:-8000}..."
export ENVIRONMENT=PROD
exec python run_admin.py --host 0.0.0.0 --port ${PORT:-8000} --no-reload