# Use official Python 3.11-slim as base
FROM mcr.microsoft.com/playwright/python:v1.41.2-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    playwright install chromium

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Start command (Note: Render startCommand override in render.yaml will take precedence)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
