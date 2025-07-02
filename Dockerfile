# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Install system dependencies and Node.js in one layer
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy package files first for better caching
COPY frontend/package*.json ./frontend/
COPY backend/requirements.txt ./backend/

# Install Node.js dependencies
WORKDIR /app/frontend
RUN npm ci --include=dev --no-audit --no-fund

# Install Python dependencies
WORKDIR /app
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application code
COPY . .

# Build Next.js frontend with optimized settings
WORKDIR /app/frontend
RUN npm run build:fast

# Copy static files to templates directory
WORKDIR /app
RUN mkdir -p templates && cp -r frontend/out/* templates/

# Set working directory back to app root
WORKDIR /app

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Start the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "1", "--timeout", "120", "backend.app:create_app()"] 