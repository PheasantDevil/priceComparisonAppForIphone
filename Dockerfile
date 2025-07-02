# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy application code
COPY . .

# Verify files exist
RUN ls -la && echo "=== Backend directory ===" && ls -la backend/ && echo "=== Frontend directory ===" && ls -la frontend/

# Install Node.js dependencies
WORKDIR /app/frontend
RUN npm ci --include=dev

# Install Python dependencies
WORKDIR /app
RUN pip install --no-cache-dir -r backend/requirements.txt

# Build Next.js frontend
WORKDIR /app/frontend
RUN npm run build

# Copy static files to templates directory
WORKDIR /app
RUN mkdir -p templates && cp -r frontend/out/* templates/

# Set working directory back to app root
WORKDIR /app

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Start the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "1", "--timeout", "120", "backend.app:create_app()"] 