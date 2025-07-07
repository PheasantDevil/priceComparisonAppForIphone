# Use Node.js 18 image as base for frontend build
FROM node:18-alpine AS frontend-builder

# Set work directory
WORKDIR /app

# Copy frontend files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Create templates directory and copy built files
RUN mkdir -p ../templates && cp -r out/* ../templates/

# Use Python 3.11 slim image for backend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy backend files
COPY backend/ ./backend/

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy templates from frontend builder
COPY --from=frontend-builder /templates ./templates

# Debug: Check if templates directory has content
RUN echo "=== Checking templates directory ===" && \
    ls -la templates/ && \
    echo "=== Checking if index.html exists ===" && \
    ls -la templates/index.html 2>/dev/null || echo "index.html not found"

# Expose port
EXPOSE $PORT

# Start the application
CMD ["python", "backend/app.py"] 