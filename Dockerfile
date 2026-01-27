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

# Start command with dynamic port
# We use python app/main.py to ensure the __main__ block and our custom diagnostics run.
CMD ["sh", "-c", "PYTHONPATH=. python app/main.py"]
