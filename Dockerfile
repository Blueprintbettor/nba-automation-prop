# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .

# Expose port
EXPOSE 8080

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/', timeout=2)"

# Run with gunicorn
CMD exec gunicorn --bind :$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    main:app
