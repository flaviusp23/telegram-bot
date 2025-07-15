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
RUN pip install --no-cache-dir --only-binary=all -r requirements.txt

# Copy application code
COPY . .

# Create directory for temp exports
RUN mkdir -p temp_exports

# Copy and make executable the Railway startup script
COPY railway-start.sh .
RUN chmod +x railway-start.sh

# Use Railway startup script
CMD ["./railway-start.sh"]