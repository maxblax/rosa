# Use Python 3.13 slim image based on Debian
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy wait-for script
COPY wait-for /bin/wait-for
RUN chmod +x /bin/wait-for

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create static files directory
RUN mkdir -p /usr/src/app/static_collected

# Expose port
EXPOSE 9000

# Default command (will be overridden by docker-compose)
CMD ["gunicorn", "rosa.wsgi:application", "--bind", "0.0.0.0:9000"]
