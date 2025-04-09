# Use base image
FROM python:3.11-slim

# Set environment variables to avoid writing .pyc files and ensure logs are displayed in real-time
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory to /app within the container
WORKDIR /app

# Install system dependencies required for building Python packages and image processing libraries
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install Python dependencies from requirements.txt without caching the downloaded packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files to the container’s /app directory
COPY . .

# Run migrations and start the Django development server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]