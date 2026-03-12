FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project configuration from root
COPY pyproject.toml poetry.lock README.md ./

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code specifically
COPY payments_service ./payments_service

# Make start script executable
RUN chmod +x payments_service/start.sh

# Expose port
EXPOSE 8000

# Set Python path to include the root /app
ENV PYTHONPATH=/app

# Command to run the application
CMD ["./payments_service/start.sh"]
