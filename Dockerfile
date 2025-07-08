FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for MySQL
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for temp exports
RUN mkdir -p temp_exports

# Run database migrations then start the bot
CMD ["sh", "-c", "alembic upgrade head && python run_bot.py"]