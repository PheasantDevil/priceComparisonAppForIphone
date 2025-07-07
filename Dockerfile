# Use Python 3.11 slim image as base
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

# Copy all files first
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Create templates directory and ensure it exists
RUN mkdir -p templates

# Verify templates directory contents
RUN ls -la templates/ || echo "Templates directory is empty or does not exist"

# Expose port
EXPOSE $PORT

# Start the application
CMD ["python", "backend/app.py"] 