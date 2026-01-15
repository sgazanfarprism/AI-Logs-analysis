# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV API_PORT=3452

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p logs results /root/.aws

# Expose the API port
EXPOSE 3452

# Default command (can be overridden)
# Options:
#   - python api.py                    (API server)
#   - python hourly_scheduler.py       (Hourly scheduler)
#   - python run_cloudwatch_analysis.py (Single run)
CMD ["python", "hourly_scheduler.py"]
