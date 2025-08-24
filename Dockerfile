# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/app/database \
    && touch /app/app/database/app.db \
    && chmod -R 777 /app/app/database

# Copy project files
COPY . .

# Set permissions for the entire app directory
RUN chmod -R 777 /app

# Expose port (mudar para 8080 para corresponder ao Easy Panel)
EXPOSE 8080

# Command to run the application (sem reload para produção)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
