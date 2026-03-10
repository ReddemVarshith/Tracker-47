# Use Python 3.13 as the base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies (Java, G++, Node.js)
RUN apt-get update && apt-get install -y \
    default-jdk \
    g++ \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "dsa_platform.wsgi:application", "--bind", "0.0.0.0:10000"]
