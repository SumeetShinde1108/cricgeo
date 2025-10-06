# Base lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dependency files (if you ever use pipenv/requirements.txt)
# COPY Pipfile Pipfile.lock /app/
# or:
# COPY requirements.txt /app/

# Install system deps required by GeoDjango
RUN apt-get update && apt-get install -y \
    binutils libproj-dev gdal-bin gcc postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Default command (placeholder)
CMD ["python3"]
